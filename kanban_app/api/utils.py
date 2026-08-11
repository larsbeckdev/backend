"""Query helpers shared by the kanban API views."""

from django.db.models import Count, Q
from rest_framework.exceptions import (NotFound, PermissionDenied,
                                       ValidationError)

from ..models import Board, Task
from .permissions import is_board_participant


def annotate_board_counts(queryset):
    """Annotate boards with the counters returned by the board list endpoint.

    The counters are aggregated in a single query. ``distinct=True`` is
    required because joining members and tasks multiplies the result rows.
    """
    return queryset.annotate(
        member_count=Count('members', distinct=True),
        ticket_count=Count('tasks', distinct=True),
        tasks_to_do_count=Count(
            'tasks', filter=Q(tasks__status=Task.Status.TO_DO), distinct=True),
        tasks_high_prio_count=Count(
            'tasks', filter=Q(tasks__priority=Task.Priority.HIGH),
            distinct=True),
    )


def task_queryset():
    """Return tasks with their related users and comment count preloaded."""
    return Task.objects.select_related(
        'assignee', 'reviewer', 'board').annotate(
            comments_count=Count('comments'))


def resolve_board(board_id, user):
    """Return the board a new task belongs to or raise the matching error.

    Missing ids fail with 400, unknown ids with 404 and boards the user
    does not participate in with 403.
    """
    if board_id in (None, ''):
        raise ValidationError({'board': 'This field is required.'})
    try:
        board = Board.objects.get(pk=board_id)
    except (Board.DoesNotExist, ValueError, TypeError):
        raise NotFound('Board not found.')
    if not is_board_participant(board, user):
        raise PermissionDenied(
            'You must be a member of this board to create a task.')
    return board


def resolve_task(task_id, user):
    """Return a task the user may access or raise 404 respectively 403."""
    try:
        task = Task.objects.select_related('board').get(pk=task_id)
    except Task.DoesNotExist:
        raise NotFound('Task not found.')
    if not is_board_participant(task.board, user):
        raise PermissionDenied(
            'You must be a member of the board this task belongs to.')
    return task


def boards_for_user(user):
    """Return the annotated boards a user owns or is a member of.

    The primary keys are resolved in a subquery so that the membership
    filter does not reuse its join for the ``member_count`` annotation.
    """
    board_ids = Board.objects.filter(
        Q(owner=user) | Q(members=user)).values('id')
    return annotate_board_counts(Board.objects.filter(pk__in=board_ids))
