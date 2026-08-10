"""Tests for listing, creating and deleting task comments."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Comment
from .factories import create_board, create_comment, create_task, create_user


class CommentListTests(APITestCase):
    """Cover GET /api/tasks/{task_id}/comments/."""

    def setUp(self):
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.stranger = create_user('stranger@example.com', 'Erika Beispiel')
        self.board = create_board(self.owner, members=[self.member])
        self.task = create_task(self.board, self.owner)
        self.url = reverse('comment-list', args=[self.task.id])
        self.client.force_authenticate(user=self.owner)

    def test_returns_comments_with_expected_fields(self):
        create_comment(self.task, self.owner)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data[0]),
                         {'id', 'created_at', 'author', 'content'})
        self.assertEqual(response.data[0]['author'], 'Max Mustermann')

    def test_comments_are_sorted_chronologically(self):
        first = create_comment(self.task, self.owner, content='Erster')
        second = create_comment(self.task, self.member, content='Zweiter')

        response = self.client.get(self.url)

        self.assertEqual([item['id'] for item in response.data],
                         [first.id, second.id])

    def test_comments_of_other_tasks_are_excluded(self):
        other_task = create_task(self.board, self.owner)
        create_comment(other_task, self.owner)

        response = self.client.get(self.url)

        self.assertEqual(response.data, [])

    def test_member_may_read_the_comments(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stranger_is_forbidden(self):
        self.client.force_authenticate(user=self.stranger)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_task_returns_404(self):
        response = self.client.get(reverse('comment-list', args=[9999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CommentCreateTests(APITestCase):
    """Cover POST /api/tasks/{task_id}/comments/."""

    def setUp(self):
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.stranger = create_user('stranger@example.com', 'Erika Beispiel')
        self.board = create_board(self.owner)
        self.task = create_task(self.board, self.owner)
        self.url = reverse('comment-list', args=[self.task.id])
        self.client.force_authenticate(user=self.owner)

    def test_creates_comment_for_the_requesting_user(self):
        payload = {'content': 'Das ist ein neuer Kommentar zur Task.'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['author'], 'Max Mustermann')
        self.assertEqual(response.data['content'], payload['content'])
        self.assertEqual(Comment.objects.get().task, self.task)

    def test_rejects_empty_content(self):
        response = self.client.post(self.url, {'content': ''}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)

    def test_rejects_whitespace_only_content(self):
        response = self.client.post(self.url, {'content': '   '},
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_missing_content(self):
        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stranger_is_forbidden(self):
        self.client.force_authenticate(user=self.stranger)

        response = self.client.post(self.url, {'content': 'Hallo'},
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_task_returns_404(self):
        response = self.client.post(reverse('comment-list', args=[9999]),
                                    {'content': 'Hallo'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CommentDeleteTests(APITestCase):
    """Cover DELETE /api/tasks/{task_id}/comments/{comment_id}/."""

    def setUp(self):
        self.owner = create_user('owner@example.com', 'Max Mustermann')
        self.member = create_user('member@example.com', 'Maxi Musterfrau')
        self.board = create_board(self.owner, members=[self.member])
        self.task = create_task(self.board, self.owner)
        self.comment = create_comment(self.task, self.member)
        self.url = reverse('comment-detail',
                           args=[self.task.id, self.comment.id])
        self.client.force_authenticate(user=self.member)

    def test_author_deletes_the_comment(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.exists())

    def test_board_owner_may_not_delete_a_foreign_comment(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.exists())

    def test_unknown_comment_returns_404(self):
        url = reverse('comment-detail', args=[self.task.id, 9999])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_of_another_task_returns_404(self):
        other_task = create_task(self.board, self.owner)
        url = reverse('comment-detail', args=[other_task.id, self.comment.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_stranger_is_forbidden(self):
        stranger = create_user('stranger@example.com', 'Erika Beispiel')
        self.client.force_authenticate(user=stranger)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
