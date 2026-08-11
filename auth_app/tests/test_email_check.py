"""Tests for the e-mail lookup endpoint."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import User


class EmailCheckTests(APITestCase):
    """Cover lookups, validation errors and the permission requirement."""

    def setUp(self):
        self.url = reverse('email-check')
        self.user = User.objects.create_user(
            email='max.mustermann@example.com',
            password='examplePassword',
            fullname='Max Mustermann',
        )
        self.client.force_authenticate(user=self.user)

    def test_returns_user_for_known_email(self):
        response = self.client.get(self.url, {'email': self.user.email})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         {'id': self.user.id, 'email': self.user.email,
                          'fullname': 'Max Mustermann'})

    def test_lookup_is_case_insensitive(self):
        response = self.client.get(
            self.url, {'email': 'MAX.MUSTERMANN@EXAMPLE.COM'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_returns_404_for_unknown_email(self):
        response = self.client.get(self.url, {'email': 'nobody@example.com'})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_returns_400_for_malformed_email(self):
        response = self.client.get(self.url, {'email': 'not-an-email'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_400_when_email_is_missing(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url, {'email': self.user.email})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
