"""API views for boards, tasks and comments."""

from django.db.models import Prefetch
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Board
from .permissions import IsBoardOwnerOrParticipant
from .serializers import (BoardCreateSerializer, BoardDetailSerializer,
                          BoardSummarySerializer, BoardUpdateSerializer)
from .utils import boards_for_user, task_queryset


class BoardListCreateView(generics.ListCreateAPIView):
    """List the boards the user participates in and create new boards."""

    queryset = Board.objects.all()
    serializer_class = BoardSummarySerializer

    def get_queryset(self):
        """Return the annotated boards the requesting user has access to."""
        return boards_for_user(self.request.user)

    def get_serializer_class(self):
        """Use the write serializer for POST and the summary for GET."""
        if self.request.method == 'POST':
            return BoardCreateSerializer
        return BoardSummarySerializer

    def create(self, request, *args, **kwargs):
        """Create the board and answer with its annotated summary."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        board = serializer.save()
        summary = BoardSummarySerializer(self.get_queryset().get(pk=board.pk))
        return Response(summary.data, status=status.HTTP_201_CREATED)


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a single board."""

    queryset = Board.objects.all()
    serializer_class = BoardDetailSerializer
    permission_classes = [IsAuthenticated, IsBoardOwnerOrParticipant]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        """Preload owner, members and tasks to keep the detail view flat."""
        return Board.objects.select_related('owner').prefetch_related(
            'members', Prefetch('tasks', queryset=task_queryset()))

    def get_serializer_class(self):
        """Use the update serializer for PATCH and the detail one otherwise."""
        if self.request.method == 'PATCH':
            return BoardUpdateSerializer
        return BoardDetailSerializer
