from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import SlugRelatedField

from reviews.models import Category, Comment, Genre, Review, Title

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "slug")


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("name", "slug")


class TitleSerializer(serializers.ModelSerializer):
    genre = SlugRelatedField(
        slug_field="slug", queryset=Genre.objects.all(), many=True
    )
    category = SlugRelatedField(
        slug_field="slug", queryset=Category.objects.all()
    )

    class Meta:
        model = Title
        fields = (
            "id",
            "name",
            "year",
            "rating",
            "description",
            "genre",
            "category",
        )

    def validate_year(self, value):
        if value > timezone.now().year:
            raise ValidationError("Год выхода произведения еще не наступил!")
        return value


class TitleDisplaySerializer(serializers.ModelSerializer):
    genre = GenreSerializer(many=True)
    category = CategorySerializer()

    class Meta:
        model = Title
        fields = (
            "id",
            "name",
            "year",
            "rating",
            "description",
            "genre",
            "category",
        )


class ReviewSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field="username", read_only="True")
    score = serializers.IntegerField(required=True)

    class Meta:
        fields = ("id", "text", "author", "score", "pub_date")
        model = Review

    def validate(self, attrs):
        user = self.context["request"].user
        title_id = self.context["view"].kwargs.get("title_id")

        if title_id is not None and self.context["request"].method != "PATCH":
            title = get_object_or_404(Title, pk=title_id)
            if user.reviews.filter(title=title).exists():
                raise ValidationError(
                    "Вы уже оставили обзор на это произведение!"
                )
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field="username", read_only="True")

    class Meta:
        fields = ("id", "text", "author", "pub_date")
        model = Comment


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "role",
            "bio",
            "first_name",
            "last_name",
        )


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email")

    def validate_username(self, value):
        if value == "me":
            raise ValidationError('Имя пользователя "me" запрещено.')
        return value


class TokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ("username", "confirmation_code")
