"""API views for registration, login and e-mail lookups."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from ..models import User
from .serializers import (LoginSerializer, RegistrationSerializer,
                          UserShortSerializer)


def build_auth_payload(user, token):
    """Return the token/user payload shared by registration and login."""
    return {
        'token': token.key,
        'fullname': user.fullname,
        'email': user.email,
        'user_id': user.id,
    }


def clean_email_parameter(raw_email):
    """Return a validated e-mail from the query string or raise a 400."""
    email = (raw_email or '').strip()
    if not email:
        raise ValidationError({'email': 'This query parameter is required.'})
    try:
        validate_email(email)
    except DjangoValidationError:
        raise ValidationError({'email': 'Enter a valid email address.'})
    return email


class RegistrationView(generics.CreateAPIView):
    """Create a new user account and return an authentication token."""

    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Persist the new user and respond with its authentication token."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(build_auth_payload(user, token),
                        status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """Authenticate a user and return an authentication token."""

    queryset = User.objects.all()
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Validate the credentials and respond with the user's token."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response(build_auth_payload(user, token),
                        status=status.HTTP_200_OK)


class EmailCheckView(generics.GenericAPIView):
    """Look up a registered user by e-mail address."""

    queryset = User.objects.all()
    serializer_class = UserShortSerializer

    def get(self, request, *args, **kwargs):
        """Return the user owning the requested e-mail address."""
        email = clean_email_parameter(request.query_params.get('email'))
        user = get_object_or_404(self.get_queryset(), email__iexact=email)
        return Response(self.get_serializer(user).data,
                        status=status.HTTP_200_OK)
