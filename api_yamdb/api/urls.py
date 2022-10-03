from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CategoriesViewSet, CommentViewSet, GenresViewSet,
                    ReviewViewSet, TitlesViewSet, UserViewSet, get_token,
                    signup)

app_name = "api"

router = DefaultRouter()
router.register(r"categories", CategoriesViewSet, basename="category")
router.register(r"genres", GenresViewSet, basename="genre")
router.register(r"titles", TitlesViewSet, basename="title")
router.register(
    r"titles/(?P<title_id>\d+)/reviews", ReviewViewSet, basename="review"
)
router.register(
    r"titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments",
    CommentViewSet,
    basename="comment",
)
router.register(r"users", UserViewSet, basename="user")


urlpatterns = [
    path("v1/auth/signup/", signup, name="signup"),
    path("v1/auth/token/", get_token, name="get_token"),
    path("v1/", include(router.urls)),
]
