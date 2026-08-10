"""Query helpers shared by the kanban API views."""

from django.db.models import Count, Q

from ..models import Board, Task


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
    return Task.objects.select_related('assignee', 'reviewer', 'board').annotate(
        comments_count=Count('comments'))


def boards_for_user(user):
    """Return the annotated boards a user owns or is a member of.

    The primary keys are resolved in a subquery so that the membership
    filter does not reuse its join for the ``member_count`` annotation.
    """
    board_ids = Board.objects.filter(
        Q(owner=user) | Q(members=user)).values('id')
    return annotate_board_counts(Board.objects.filter(pk__in=board_ids))
