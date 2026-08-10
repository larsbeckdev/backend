"""Database models for the authentication app."""

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """Application user identified by a unique e-mail address.

    The KanMind frontend only ever submits ``fullname`` and ``email``, so the
    default ``username``/``first_name``/``last_name`` fields are dropped in
    favour of a single ``fullname`` field.
    """

    username = None
    first_name = None
    last_name = None

    email = models.EmailField('email address', unique=True)
    fullname = models.CharField('full name', max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname']

    objects = UserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['fullname']

    def __str__(self):
        return f'{self.fullname} ({self.email})'

    def get_full_name(self):
        """Return the display name used by Django's admin and auth helpers."""
        return self.fullname

    def get_short_name(self):
        """Return the short display name used by Django's auth helpers."""
        return self.fullname
