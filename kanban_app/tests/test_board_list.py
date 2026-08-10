"""Tests for listing and creating boards."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Board, Task
from .factories import create_board, create_task, create_user


class BoardListTests(APITestCase):
    """Cover GET /api/boards/."""

    def setUp(self):
        self.url = reverse('board-list')
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.stranger = create_user('stranger@example.com', 'Erika Beispiel')
        self.board = create_board(self.owner, members=[self.member])
        self.client.force_authenticate(user=self.owner)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_sees_own_board_with_expected_fields(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(set(response.data[0]), {
            'id', 'title', 'member_count', 'ticket_count',
            'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id'})
        self.assertEqual(response.data[0]['owner_id'], self.owner.id)

    def test_member_sees_the_shared_board(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.get(self.url)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.board.id)

    def test_stranger_sees_no_boards(self):
        self.client.force_authenticate(user=self.stranger)

        response = self.client.get(self.url)

        self.assertEqual(response.data, [])

    def test_counts_are_calculated_per_board(self):
        create_task(self.board, self.owner, status=Task.Status.TO_DO,
                    priority=Task.Priority.HIGH)
        create_task(self.board, self.owner, status=Task.Status.TO_DO)
        create_task(self.board, self.owner, status=Task.Status.DONE)

        board_data = self.client.get(self.url).data[0]

        self.assertEqual(board_data['member_count'], 1)
        self.assertEqual(board_data['ticket_count'], 3)
        self.assertEqual(board_data['tasks_to_do_count'], 2)
        self.assertEqual(board_data['tasks_high_prio_count'], 1)

    def test_member_count_is_not_reduced_by_the_membership_filter(self):
        second_member = create_user('second@example.com', 'Moritz Muster')
        self.board.members.add(second_member)
        self.client.force_authenticate(user=self.member)

        board_data = self.client.get(self.url).data[0]

        self.assertEqual(board_data['member_count'], 2)

    def test_board_is_listed_once_for_an_owning_member(self):
        self.board.members.add(self.owner)

        response = self.client.get(self.url)

        self.assertEqual(len(response.data), 1)


class BoardCreateTests(APITestCase):
    """Cover POST /api/boards/."""

    def setUp(self):
        self.url = reverse('board-list')
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.client.force_authenticate(user=self.owner)

    def test_creates_board_and_returns_summary(self):
        payload = {'title': 'Neues Projekt', 'members': [self.member.id]}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Neues Projekt')
        self.assertEqual(response.data['member_count'], 1)
        self.assertEqual(response.data['ticket_count'], 0)
        self.assertEqual(response.data['owner_id'], self.owner.id)

    def test_requesting_user_becomes_the_owner(self):
        self.client.post(self.url, {'title': 'Neues Projekt'}, format='json')

        self.assertEqual(Board.objects.get().owner, self.owner)

    def test_members_are_optional(self):
        response = self.client.post(self.url, {'title': 'Solo'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['member_count'], 0)

    def test_rejects_missing_title(self):
        response = self.client.post(self.url, {'members': []}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_rejects_unknown_member_id(self):
        payload = {'title': 'Neues Projekt', 'members': [9999]}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('members', response.data)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url, {'title': 'X'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
