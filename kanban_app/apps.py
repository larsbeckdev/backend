"""Application configuration for the kanban app."""

from django.apps import AppConfig


class KanbanAppConfig(AppConfig):
    """Configuration for the ``kanban_app`` application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kanban_app'
    verbose_name = 'Kanban'
