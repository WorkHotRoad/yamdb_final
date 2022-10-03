from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, pagination, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api_yamdb.settings import DOMAIN_NAME
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Genre, Review, Title

from .filters import TitleFilter
from .permissions import AdminOrReadOnly, IsAdmin, StaffOrAuthorOrReadOnly
from .serializers import (AdminSerializer, CategorySerializer,
                          CommentSerializer, GenreSerializer, ReviewSerializer,
                          SignupSerializer, TitleDisplaySerializer,
                          TitleSerializer, TokenSerializer)

User = get_user_model()


class ListCreateDestroyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    pass


class CommentViewSet(viewsets.ModelViewSet):
    """Комментарии к отзывам."""

    serializer_class = CommentSerializer
    permission_classes = (StaffOrAuthorOrReadOnly,)
    pagination_class = pagination.LimitOffsetPagination

    def get_queryset(self):
        review_id = self.kwargs.get("review_id")
        review = get_object_or_404(Review, pk=review_id)
        return review.comments.all()

    def perform_create(self, serializer):
        review_id = self.kwargs.get("review_id")
        review = get_object_or_404(Review, pk=review_id)
        serializer.save(review=review, author=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    """Только одно ревью к одному фильму."""

    serializer_class = ReviewSerializer
    permission_classes = [StaffOrAuthorOrReadOnly]
    pagination_class = pagination.LimitOffsetPagination

    def get_queryset(self):
        title_id = self.kwargs.get("title_id")
        title = get_object_or_404(Title, pk=title_id)
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get("title_id")
        title = get_object_or_404(Title, pk=title_id)
        serializer.save(author=self.request.user, title=title)


class CategoriesViewSet(ListCreateDestroyViewSet):
    """Получить список категорий, добавить или удалить категорию."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = (AdminOrReadOnly,)
    pagination_class = pagination.LimitOffsetPagination

    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)


class GenresViewSet(ListCreateDestroyViewSet):
    """Получить список жанров, добавить или удалить жанр."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = "slug"
    permission_classes = (AdminOrReadOnly,)
    pagination_class = pagination.LimitOffsetPagination

    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)


class TitlesViewSet(viewsets.ModelViewSet):
    """Получить список произведений и данные по одному произведению.

    Также Добавить произведение, изменить и удалить его.
    """

    queryset = Title.objects.all()
    permission_classes = (AdminOrReadOnly,)
    pagination_class = pagination.LimitOffsetPagination

    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return TitleDisplaySerializer
        return TitleSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    """Принимает почту и юзернейм, в ответ отправляет код подтверждения."""
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = User.objects.create(
        email=serializer.validated_data["email"],
        username=serializer.validated_data["username"],
    )

    confirmation_code = default_token_generator.make_token(user)
    confirmation_code_hashed = make_password(
        confirmation_code, salt="well"
    )

    user.confirmation_code = confirmation_code_hashed
    user.save()

    send_mail(
        "Код подтверждения",
        f"{user.username}, код: {confirmation_code} /api/v1/auth/token/",
        DOMAIN_NAME,
        [f"{user.email}"],
    )
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([AllowAny])
def get_token(request):
    """Принимает код подтверждения, сравнивает его с хешем.

    В ответ отправляет токен.
    """
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.data["username"]
    user = get_object_or_404(User, username=username)
    c_code = serializer.validated_data["confirmation_code"]
    if check_password(c_code, user.confirmation_code):
        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token)})
    raise ValidationError(f"Неверный код подтверждения: {c_code}!")


class UserViewSet(viewsets.ModelViewSet):
    """Админ может получить список пользователей, добаввить одного.

    Получить, изменить его данные. Удалить его. Сам пользователь может
    получить и изменить свои данные.
    """

    queryset = User.objects.all()
    serializer_class = AdminSerializer
    permission_classes = (IsAdmin,)
    lookup_field = "username"
    filter_backends = (filters.SearchFilter,)
    search_fields = ("username",)

    @action(
        detail=False,
        methods=["get", "patch"],
        url_path="me",
        url_name="me",
        permission_classes=(IsAuthenticated,),
    )
    def about_me(self, request):
        serializer = AdminSerializer(request.user)
        if request.method == "PATCH":
            serializer = AdminSerializer(
                request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)

            role_user = request.user.role
            if role_user == "moderator" or role_user == "user":
                serializer.validated_data["role"] = role_user
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
