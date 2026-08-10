"""Serializers for registration, login and user lookups."""

from django.contrib.auth import authenticate
from rest_framework import serializers

from ..models import User


class UserShortSerializer(serializers.ModelSerializer):
    """Compact user representation embedded in board and task payloads."""

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate and create a new user account."""

    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 8}}

    def validate_email(self, value):
        """Reject e-mail addresses that are already registered."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'This email address is already registered.')
        return value

    def validate(self, attrs):
        """Ensure both submitted passwords are identical."""
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                {'repeated_password': 'The passwords do not match.'})
        return attrs

    def create(self, validated_data):
        """Create the user with a properly hashed password."""
        validated_data.pop('repeated_password')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Authenticate a user by e-mail and password."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Attach the authenticated user or reject the credentials."""
        user = authenticate(
            request=self.context.get('request'),
            email=attrs['email'],
            password=attrs['password'],
        )
        if user is None:
            raise serializers.ValidationError(
                {'detail': 'Invalid email or password.'})
        attrs['user'] = user
        return attrs
