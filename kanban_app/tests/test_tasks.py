"""Tests for creating, updating, deleting and listing tasks."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Task
from .factories import (create_board, create_comment, create_task,
                        create_user)

TASK_FIELDS = {'id', 'board', 'title', 'description', 'status', 'priority',
               'assignee', 'reviewer', 'due_date', 'comments_count'}


class TaskCreateTests(APITestCase):
    """Cover POST /api/tasks/."""

    def setUp(self):
        self.url = reverse('task-create')
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.stranger = create_user('stranger@example.com', 'Erika Beispiel')
        self.board = create_board(self.owner, members=[self.member])
        self.client.force_authenticate(user=self.owner)
        self.payload = {
            'board': self.board.id,
            'title': 'Code-Review durchfuehren',
            'description': 'Den neuen PR pruefen',
            'status': 'review',
            'priority': 'medium',
            'assignee_id': self.member.id,
            'reviewer_id': self.owner.id,
            'due_date': '2025-02-27',
        }

    def test_creates_task_with_expected_payload(self):
        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data), TASK_FIELDS)
        self.assertEqual(response.data['board'], self.board.id)
        self.assertEqual(response.data['assignee']['id'], self.member.id)
        self.assertEqual(response.data['reviewer']['id'], self.owner.id)
        self.assertEqual(response.data['comments_count'], 0)

    def test_records_the_creator(self):
        self.client.post(self.url, self.payload, format='json')

        self.assertEqual(Task.objects.get().created_by, self.owner)

    def test_assignee_and_reviewer_are_optional(self):
        payload = {k: v for k, v in self.payload.items()
                   if k not in ('assignee_id', 'reviewer_id')}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['assignee'])
        self.assertIsNone(response.data['reviewer'])

    def test_accepts_explicit_null_users(self):
        payload = {**self.payload, 'assignee_id': None, 'reviewer_id': None}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_rejects_assignee_outside_the_board(self):
        payload = {**self.payload, 'assignee_id': self.stranger.id}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('assignee_id', response.data)

    def test_rejects_reviewer_outside_the_board(self):
        payload = {**self.payload, 'reviewer_id': self.stranger.id}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reviewer_id', response.data)

    def test_rejects_invalid_status(self):
        payload = {**self.payload, 'status': 'archived'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data)

    def test_rejects_invalid_priority(self):
        payload = {**self.payload, 'priority': 'urgent'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('priority', response.data)

    def test_rejects_missing_board(self):
        payload = {k: v for k, v in self.payload.items() if k != 'board'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_board_returns_404(self):
        payload = {**self.payload, 'board': 9999}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_numeric_board_returns_404(self):
        payload = {**self.payload, 'board': 'abc'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_stranger_is_forbidden(self):
        self.client.force_authenticate(user=self.stranger)

        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskUpdateTests(APITestCase):
    """Cover PATCH /api/tasks/{task_id}/."""

    def setUp(self):
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.stranger = create_user('stranger@example.com', 'Erika Beispiel')
        self.board = create_board(self.owner, members=[self.member])
        self.task = create_task(self.board, self.owner)
        self.url = reverse('task-detail', args=[self.task.id])
        self.client.force_authenticate(user=self.owner)

    def test_updates_task_and_returns_documented_fields(self):
        payload = {'title': 'Code-Review abschliessen', 'status': 'done',
                   'priority': 'high', 'due_date': '2025-02-28'}

        response = self.client.patch(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {
            'id', 'title', 'description', 'status', 'priority', 'assignee',
            'reviewer', 'due_date'})
        self.assertEqual(response.data['status'], 'done')

    def test_updates_a_single_field(self):
        response = self.client.patch(self.url, {'status': 'in-progress'},
                                     format='json')

        self.task.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.task.status, 'in-progress')

    def test_board_field_in_payload_is_ignored(self):
        other_board = create_board(self.owner, title='Anderes Board')

        self.client.patch(self.url, {'board': other_board.id}, format='json')

        self.task.refresh_from_db()
        self.assertEqual(self.task.board, self.board)

    def test_assigns_a_board_member(self):
        response = self.client.patch(self.url,
                                     {'assignee_id': self.member.id},
                                     format='json')

        self.assertEqual(response.data['assignee']['id'], self.member.id)

    def test_rejects_assignee_outside_the_board(self):
        response = self.client.patch(self.url,
                                     {'assignee_id': self.stranger.id},
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_reviewer_outside_the_board(self):
        response = self.client.patch(self.url,
                                     {'reviewer_id': self.stranger.id},
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_member_may_update_the_task(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.patch(self.url, {'status': 'done'},
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stranger_is_forbidden(self):
        self.client.force_authenticate(user=self.stranger)

        response = self.client.patch(self.url, {'status': 'done'},
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_task_returns_404(self):
        response = self.client.patch(reverse('task-detail', args=[9999]),
                                     {'status': 'done'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.patch(self.url, {'status': 'done'},
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskDeleteTests(APITestCase):
    """Cover DELETE /api/tasks/{task_id}/."""

    def setUp(self):
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.board = create_board(self.owner, members=[self.member])
        self.task = create_task(self.board, created_by=self.member)
        self.url = reverse('task-detail', args=[self.task.id])

    def test_creator_deletes_the_task(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.exists())

    def test_board_owner_deletes_the_task(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_other_member_may_not_delete_the_task(self):
        other = create_user('other@example.com', 'Moritz Muster')
        self.board.members.add(other)
        self.client.force_authenticate(user=other)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Task.objects.exists())

    def test_requires_authentication(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskListTests(APITestCase):
    """Cover GET /api/tasks/assigned-to-me/ and /api/tasks/reviewing/."""

    def setUp(self):
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.board = create_board(self.owner, members=[self.member])
        self.assigned = create_task(self.board, self.owner,
                                    assignee=self.member,
                                    reviewer=self.owner)
        self.reviewing = create_task(self.board, self.owner,
                                     reviewer=self.member)
        self.client.force_authenticate(user=self.member)

    def test_assigned_list_returns_only_own_tasks(self):
        response = self.client.get(reverse('task-assigned-to-me'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([task['id'] for task in response.data],
                         [self.assigned.id])
        self.assertEqual(set(response.data[0]), TASK_FIELDS)

    def test_reviewing_list_returns_only_own_reviews(self):
        response = self.client.get(reverse('task-reviewing'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([task['id'] for task in response.data],
                         [self.reviewing.id])

    def test_lists_include_the_comment_count(self):
        create_comment(self.assigned, self.owner)

        response = self.client.get(reverse('task-assigned-to-me'))

        self.assertEqual(response.data[0]['comments_count'], 1)

    def test_other_user_sees_an_empty_assigned_list(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.get(reverse('task-assigned-to-me'))

        self.assertEqual(response.data, [])

    def test_assigned_list_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse('task-assigned-to-me'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reviewing_list_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse('task-reviewing'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
