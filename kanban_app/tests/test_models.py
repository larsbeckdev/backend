"""Tests for the kanban models and the demo data command."""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from auth_app.models import User

from ..models import Board, Comment, Task
from .factories import create_board, create_comment, create_task, create_user


class ModelStringTests(TestCase):
    """Cover the human readable representation of every model."""

    def setUp(self):
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.board = create_board(self.owner, title='Projekt X')
        self.task = create_task(self.board, self.owner, title='Task 1')

    def test_board_str_is_its_title(self):
        self.assertEqual(str(self.board), 'Projekt X')

    def test_task_str_is_its_title(self):
        self.assertEqual(str(self.task), 'Task 1')

    def test_comment_str_names_author_and_task(self):
        comment = create_comment(self.task, self.owner)

        self.assertEqual(str(comment), f'{self.owner} on {self.task}')


class ModelRelationTests(TestCase):
    """Cover the cascade and null behaviour of the relations."""

    def setUp(self):
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.board = create_board(self.owner, members=[self.member])
        self.task = create_task(self.board, self.owner,
                                assignee=self.member)

    def test_deleting_a_board_cascades_to_tasks_and_comments(self):
        create_comment(self.task, self.owner)

        self.board.delete()

        self.assertFalse(Task.objects.exists())
        self.assertFalse(Comment.objects.exists())

    def test_deleting_an_assignee_keeps_the_task(self):
        self.member.delete()
        self.task.refresh_from_db()

        self.assertIsNone(self.task.assignee)

    def test_tasks_are_reachable_through_the_related_name(self):
        self.assertEqual(list(self.board.tasks.all()), [self.task])


class SeedDemoCommandTests(TestCase):
    """Cover the seed_demo management command."""

    def test_creates_users_board_tasks_and_comments(self):
        call_command('seed_demo', stdout=StringIO())

        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Board.objects.count(), 1)
        self.assertEqual(Task.objects.count(), 4)
        self.assertEqual(Comment.objects.count(), 4)

    def test_running_it_twice_does_not_duplicate_data(self):
        call_command('seed_demo', stdout=StringIO())
        call_command('seed_demo', stdout=StringIO())

        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Board.objects.count(), 1)
        self.assertEqual(Task.objects.count(), 4)

    def test_guest_account_can_log_in(self):
        call_command('seed_demo', stdout=StringIO())
        guest = User.objects.get(email='kevin@kovacsi.de')

        self.assertTrue(guest.check_password('asdasdasd'))
