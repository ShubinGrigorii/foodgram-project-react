from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q, F

from foods.validators import validate_username


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=(validate_username,)
    )

    def __str__(self):
        return self.username

    class Meta:
        ordering = ('id',)


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_name_author'),
            models.CheckConstraint(
                check=~Q(user=F('author')),
                name='check_author'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.author.username}'
