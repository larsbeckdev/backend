"""Object managers for the authentication app."""

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Create users that are identified by their e-mail address."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        """Create and persist a regular user with a normalized e-mail."""
        if not email:
            raise ValueError('Users require an email address.')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and persist a user with full administrative access."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusers require is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusers require is_superuser=True.')
        return self.create_user(email, password, **extra_fields)
