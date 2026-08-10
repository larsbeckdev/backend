"""Tests for the login endpoint."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import User


class LoginTests(APITestCase):
    """Cover successful authentication and rejected credentials."""

    def setUp(self):
        self.url = reverse('login')
        self.user = User.objects.create_user(
            email='max.mustermann@example.com',
            password='examplePassword',
            fullname='Max Mustermann',
        )

    def test_login_returns_token_and_user_data(self):
        payload = {'email': self.user.email, 'password': 'examplePassword'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertEqual(response.data['fullname'], 'Max Mustermann')
        self.assertTrue(response.data['token'])

    def test_login_returns_the_same_token_twice(self):
        payload = {'email': self.user.email, 'password': 'examplePassword'}

        first = self.client.post(self.url, payload, format='json')
        second = self.client.post(self.url, payload, format='json')

        self.assertEqual(first.data['token'], second.data['token'])

    def test_login_rejects_wrong_password(self):
        payload = {'email': self.user.email, 'password': 'wrongPassword'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_rejects_unknown_email(self):
        payload = {'email': 'nobody@example.com', 'password': 'examplePassword'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_rejects_missing_password(self):
        response = self.client.post(self.url, {'email': self.user.email},
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
