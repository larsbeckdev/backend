"""Application configuration for the authentication app."""

from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """Configuration for the ``auth_app`` application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_app'
    verbose_name = 'Authentication'
