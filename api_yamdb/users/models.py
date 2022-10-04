from django.contrib.auth.models import AbstractUser
from django.db import models
from reviews.validators import validate_username

USER = "user"
ADMIN = "admin"
MODERATOR = "moderator"


class User(AbstractUser):
    ROLE_CHOICES = [
        (USER, USER),
        (ADMIN, ADMIN),
        (MODERATOR, MODERATOR),
    ]

    username = models.CharField(
        validators=(validate_username,), max_length=200, unique=True
    )
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=USER,
    )
    confirmation_code = models.CharField(max_length=30)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["username"]
