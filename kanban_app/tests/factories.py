"""Object factories shared by the kanban tests."""

from datetime import date

from auth_app.models import User

from ..models import Board, Comment, Task

DEFAULT_PASSWORD = 'examplePassword'
DEFAULT_DUE_DATE = date(2025, 2, 25)


def create_user(email='user@example.com', fullname='Test User'):
    """Create a user with a known password."""
    return User.objects.create_user(
        email=email, password=DEFAULT_PASSWORD, fullname=fullname)


def create_board(owner, title='Projekt X', members=()):
    """Create a board owned by ``owner`` with the given members."""
    board = Board.objects.create(owner=owner, title=title)
    board.members.set(members)
    return board


def create_task(board, created_by=None, **overrides):
    """Create a task on ``board`` using sensible defaults."""
    data = {
        'title': 'API-Dokumentation schreiben',
        'description': 'Die API-Dokumentation vervollstaendigen',
        'status': Task.Status.TO_DO,
        'priority': Task.Priority.MEDIUM,
        'due_date': DEFAULT_DUE_DATE,
    }
    data.update(overrides)
    return Task.objects.create(board=board, created_by=created_by, **data)


def create_comment(task, author, content='Das ist ein Kommentar zur Task.'):
    """Create a comment written by ``author`` on ``task``."""
    return Comment.objects.create(task=task, author=author, content=content)
