from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.utils import timezone

User = get_user_model()


class Genre(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(
        max_length=50, unique=True, verbose_name="Имя ссылки"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Жанр"


class Category(models.Model):
    name = models.CharField(max_length=256, verbose_name="Категория")
    slug = models.SlugField(
        max_length=50, unique=True, verbose_name="Имя ссылки"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Категория"


class Title(models.Model):
    name = models.CharField(max_length=64)
    year = models.PositiveSmallIntegerField(verbose_name="Год выхода")
    rating = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name="Рейтинг"
    )
    description = models.TextField(
        blank=True, null=True, verbose_name="Описание"
    )
    genre = models.ManyToManyField(
        Genre, through="GenreTitle", related_name="titles"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, blank=True, null=True
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(year__lte=timezone.now().year),
                name="year_lte_now",
            )
        ]
        ordering = ["name"]
        verbose_name = "Название"

    @property
    def rating(self):
        return self.reviews.aggregate(Avg("score"))["score__avg"]


class GenreTitle(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
    )
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name="reviews",
        db_constraint=False,
    )
    text = models.TextField(verbose_name="Текст")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Автор",
    )
    score = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        error_messages={"validators": "От одного до десяти!"},
        verbose_name="Оценка",
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="Дата публикации"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["title", "author"], name="unique author review"
            )
        ]

        ordering = ["-pub_date"]
        verbose_name = "Обзор"


class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField(verbose_name="Текст")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="Дата публикации"
    )

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Комментарии"
