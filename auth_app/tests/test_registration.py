"""Tests for the registration endpoint."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import User

VALID_PAYLOAD = {
    'fullname': 'Max Mustermann',
    'email': 'max.mustermann@example.com',
    'password': 'examplePassword',
    'repeated_password': 'examplePassword',
}


class RegistrationTests(APITestCase):
    """Cover successful registration and its validation errors."""

    def setUp(self):
        self.url = reverse('registration')

    def test_registration_creates_user_and_returns_token(self):
        response = self.client.post(self.url, VALID_PAYLOAD, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data),
                         {'token', 'fullname', 'email', 'user_id'})
        self.assertEqual(response.data['email'], VALID_PAYLOAD['email'])
        self.assertTrue(User.objects.filter(email=VALID_PAYLOAD['email']).exists())

    def test_registration_hashes_the_password(self):
        self.client.post(self.url, VALID_PAYLOAD, format='json')
        user = User.objects.get(email=VALID_PAYLOAD['email'])

        self.assertNotEqual(user.password, VALID_PAYLOAD['password'])
        self.assertTrue(user.check_password(VALID_PAYLOAD['password']))

    def test_registration_rejects_mismatched_passwords(self):
        payload = {**VALID_PAYLOAD, 'repeated_password': 'somethingElse'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('repeated_password', response.data)

    def test_registration_rejects_duplicate_email(self):
        self.client.post(self.url, VALID_PAYLOAD, format='json')

        response = self.client.post(self.url, VALID_PAYLOAD, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_rejects_email_differing_only_in_case(self):
        self.client.post(self.url, VALID_PAYLOAD, format='json')
        payload = {**VALID_PAYLOAD, 'email': 'MAX.MUSTERMANN@EXAMPLE.COM'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_registration_rejects_missing_fields(self):
        response = self.client.post(self.url, {'email': 'a@b.de'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fullname', response.data)

    def test_registration_rejects_short_password(self):
        payload = {**VALID_PAYLOAD, 'password': 'short', 'repeated_password': 'short'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
