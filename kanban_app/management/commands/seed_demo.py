"""Management command that fills the database with demo content."""

from datetime import date, timedelta

from django.core.management.base import BaseCommand

from auth_app.models import User

from ...models import Board, Comment, Task

DEMO_USERS = [
    ('kevin@kovacsi.de', 'Kevin Kovacsi', 'asdasdasd'),
    ('max.mustermann@example.com', 'Max Mustermann', 'asdasdasd'),
    ('maxi.musterfrau@example.com', 'Maxi Musterfrau', 'asdasdasd'),
]

DEMO_TASKS = [
    ('API-Dokumentation schreiben', 'to-do', 'high', 0, 1),
    ('Code-Review durchfuehren', 'review', 'medium', 1, 2),
    ('Login-Formular stylen', 'in-progress', 'low', 2, 0),
    ('Deployment vorbereiten', 'done', 'medium', 1, 0),
]


class Command(BaseCommand):
    """Create a guest account, a demo board, tasks and comments."""

    help = 'Create demo users, one board with tasks and a few comments.'

    def handle(self, *args, **options):
        """Build the demo data set and report the result."""
        users = [self.create_user(*entry) for entry in DEMO_USERS]
        board = self.create_board(users)
        self.create_tasks(board, users)
        self.stdout.write(self.style.SUCCESS(
            f'Demo data ready. Guest login: {DEMO_USERS[0][0]} / '
            f'{DEMO_USERS[0][2]}'))

    def create_user(self, email, fullname, password):
        """Return the demo user, creating it on the first run."""
        user = User.objects.filter(email=email).first()
        if user is None:
            user = User.objects.create_user(
                email=email, fullname=fullname, password=password)
        return user

    def create_board(self, users):
        """Return the demo board owned by the guest account."""
        board, _ = Board.objects.get_or_create(
            title='Projekt X', owner=users[0])
        board.members.set(users)
        return board

    def create_tasks(self, board, users):
        """Create the demo tasks and one comment per created task."""
        if board.tasks.exists():
            return
        for offset, entry in enumerate(DEMO_TASKS):
            task = self.create_task(board, users, offset, entry)
            Comment.objects.create(
                task=task, author=users[0],
                content='Das ist ein Kommentar zur Task.')

    def create_task(self, board, users, offset, entry):
        """Create a single demo task from a definition tuple."""
        title, task_status, priority, assignee, reviewer = entry
        return Task.objects.create(
            board=board, title=title, description=f'Demo task: {title}',
            status=task_status, priority=priority,
            assignee=users[assignee], reviewer=users[reviewer],
            created_by=users[0],
            due_date=date.today() + timedelta(days=offset + 1))
