"""Database models for boards, tasks and comments."""

from django.conf import settings
from django.db import models


class Board(models.Model):
    """A kanban board owned by one user and shared with its members."""

    title = models.CharField('title', max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_boards',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='boards',
        blank=True,
    )
    created_at = models.DateTimeField('created at', auto_now_add=True)

    class Meta:
        verbose_name = 'board'
        verbose_name_plural = 'boards'
        ordering = ['id']

    def __str__(self):
        return self.title


class Task(models.Model):
    """A single ticket on a board."""

    class Status(models.TextChoices):
        TO_DO = 'to-do', 'To do'
        IN_PROGRESS = 'in-progress', 'In progress'
        REVIEW = 'review', 'Review'
        DONE = 'done', 'Done'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    title = models.CharField('title', max_length=255)
    description = models.TextField('description', blank=True, default='')
    status = models.CharField('status', max_length=20, choices=Status.choices)
    priority = models.CharField('priority', max_length=10,
                                choices=Priority.choices)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_tasks',
        null=True,
        blank=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviewing_tasks',
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_tasks',
        null=True,
        blank=True,
    )
    due_date = models.DateField('due date')
    created_at = models.DateTimeField('created at', auto_now_add=True)

    class Meta:
        verbose_name = 'task'
        verbose_name_plural = 'tasks'
        ordering = ['id']

    def __str__(self):
        return self.title


class Comment(models.Model):
    """A chronological comment written by a board member on a task."""

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    content = models.TextField('content')
    created_at = models.DateTimeField('created at', auto_now_add=True)

    class Meta:
        verbose_name = 'comment'
        verbose_name_plural = 'comments'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} on {self.task}'
