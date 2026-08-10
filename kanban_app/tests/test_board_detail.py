"""Tests for retrieving, updating and deleting a single board."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Board, Task
from .factories import create_board, create_comment, create_task, create_user


class BoardDetailTests(APITestCase):
    """Cover GET /api/boards/{board_id}/."""

    def setUp(self):
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.stranger = create_user('stranger@example.com', 'Erika Beispiel')
        self.board = create_board(self.owner, members=[self.member])
        self.url = reverse('board-detail', args=[self.board.id])
        self.client.force_authenticate(user=self.owner)

    def test_returns_board_with_members_and_tasks(self):
        create_task(self.board, self.owner, reviewer=self.owner)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data),
                         {'id', 'title', 'owner_id', 'members', 'tasks'})
        self.assertEqual(response.data['owner_id'], self.owner.id)
        self.assertEqual(len(response.data['members']), 1)
        self.assertEqual(len(response.data['tasks']), 1)

    def test_embedded_task_omits_the_board_field(self):
        create_task(self.board, self.owner)

        task_data = self.client.get(self.url).data['tasks'][0]

        self.assertEqual(set(task_data), {
            'id', 'title', 'description', 'status', 'priority', 'assignee',
            'reviewer', 'due_date', 'comments_count'})

    def test_embedded_task_counts_its_comments(self):
        task = create_task(self.board, self.owner)
        create_comment(task, self.owner)
        create_comment(task, self.member)

        task_data = self.client.get(self.url).data['tasks'][0]

        self.assertEqual(task_data['comments_count'], 2)

    def test_unassigned_task_returns_null_users(self):
        create_task(self.board, self.owner)

        task_data = self.client.get(self.url).data['tasks'][0]

        self.assertIsNone(task_data['assignee'])
        self.assertIsNone(task_data['reviewer'])

    def test_member_may_read_the_board(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stranger_is_forbidden(self):
        self.client.force_authenticate(user=self.stranger)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_board_returns_404(self):
        response = self.client.get(reverse('board-detail', args=[9999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BoardUpdateTests(APITestCase):
    """Cover PATCH /api/boards/{board_id}/."""

    def setUp(self):
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.stranger = create_user('stranger@example.com', 'Erika Beispiel')
        self.board = create_board(self.owner, members=[self.member])
        self.url = reverse('board-detail', args=[self.board.id])
        self.client.force_authenticate(user=self.owner)

    def test_updates_title_and_returns_owner_and_member_data(self):
        response = self.client.patch(self.url, {'title': 'Changed title'},
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data),
                         {'id', 'title', 'owner_data', 'members_data'})
        self.assertEqual(response.data['title'], 'Changed title')
        self.assertEqual(response.data['owner_data']['id'], self.owner.id)

    def test_title_only_patch_keeps_the_members(self):
        self.client.patch(self.url, {'title': 'Changed title'}, format='json')

        self.assertEqual(self.board.members.count(), 1)

    def test_members_are_replaced_by_the_submitted_list(self):
        new_member = create_user('new@example.com', 'Moritz Muster')

        response = self.client.patch(self.url, {'members': [new_member.id]},
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(self.board.members.all()), [new_member])

    def test_members_can_be_emptied(self):
        self.client.patch(self.url, {'members': []}, format='json')

        self.assertEqual(self.board.members.count(), 0)

    def test_member_may_update_the_board(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.patch(self.url, {'title': 'By member'},
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stranger_is_forbidden(self):
        self.client.force_authenticate(user=self.stranger)

        response = self.client.patch(self.url, {'title': 'Nope'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rejects_unknown_member_id(self):
        response = self.client.patch(self.url, {'members': [9999]},
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_is_not_allowed(self):
        response = self.client.put(self.url, {'title': 'X'}, format='json')

        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)


class BoardDeleteTests(APITestCase):
    """Cover DELETE /api/boards/{board_id}/."""

    def setUp(self):
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.board = create_board(self.owner, members=[self.member])
        self.url = reverse('board-detail', args=[self.board.id])
        self.client.force_authenticate(user=self.owner)

    def test_owner_deletes_the_board(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Board.objects.exists())

    def test_deleting_a_board_removes_its_tasks_and_comments(self):
        task = create_task(self.board, self.owner)
        create_comment(task, self.owner)

        self.client.delete(self.url)

        self.assertFalse(Task.objects.exists())

    def test_member_may_not_delete_the_board(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Board.objects.exists())

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
