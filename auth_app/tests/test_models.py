"""Tests for the user model and its manager."""

from django.test import TestCase

from ..models import User


class UserManagerTests(TestCase):
    """Cover the creation helpers of the custom user manager."""

    def test_create_user_normalizes_the_email_domain(self):
        user = User.objects.create_user(
            email='Max@EXAMPLE.COM', password='examplePassword',
            fullname='Max Mustermann')

        self.assertEqual(user.email, 'Max@example.com')

    def test_create_user_is_not_staff_by_default(self):
        user = User.objects.create_user(
            email='max@example.com', password='examplePassword',
            fullname='Max Mustermann')

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_requires_an_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='', password='examplePassword', fullname='No Mail')

    def test_create_superuser_sets_both_flags(self):
        admin = User.objects.create_superuser(
            email='admin@example.com', password='examplePassword',
            fullname='Admin User')

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_create_superuser_rejects_is_staff_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com', password='examplePassword',
                fullname='Admin User', is_staff=False)

    def test_create_superuser_rejects_is_superuser_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com', password='examplePassword',
                fullname='Admin User', is_superuser=False)


class UserModelTests(TestCase):
    """Cover the display helpers of the user model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='max@example.com', password='examplePassword',
            fullname='Max Mustermann')

    def test_str_contains_name_and_email(self):
        self.assertEqual(str(self.user), 'Max Mustermann (max@example.com)')

    def test_full_and_short_name_return_the_fullname(self):
        self.assertEqual(self.user.get_full_name(), 'Max Mustermann')
        self.assertEqual(self.user.get_short_name(), 'Max Mustermann')

    def test_email_is_the_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, 'email')
        self.assertEqual(self.user.get_username(), 'max@example.com')
