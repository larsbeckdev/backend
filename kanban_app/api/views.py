"""API views for boards, tasks and comments."""

from django.db.models import Prefetch
from django.utils.functional import cached_property
from rest_framework import generics, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Board, Task
from .permissions import IsBoardOwnerOrParticipant, IsTaskBoardParticipant
from .serializers import (BoardCreateSerializer, BoardDetailSerializer,
                          BoardSummarySerializer, BoardUpdateSerializer,
                          TaskCreateSerializer, TaskSerializer,
                          TaskUpdateSerializer)
from .utils import boards_for_user, resolve_board, task_queryset


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


class TaskCreateView(generics.CreateAPIView):
    """Create a task on a board the requesting user participates in."""

    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer

    @cached_property
    def target_board(self):
        """Resolve the board named in the payload exactly once per request."""
        return resolve_board(self.request.data.get('board'), self.request.user)

    def get_serializer_context(self):
        """Add the resolved target board to the serializer context."""
        context = super().get_serializer_context()
        context['board'] = self.target_board
        return context

    def perform_create(self, serializer):
        """Store the task on the resolved board and record its creator."""
        serializer.save(board=self.target_board, created_by=self.request.user)


class TaskDetailView(mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                     generics.GenericAPIView):
    """Update or delete a single task."""

    queryset = Task.objects.all()
    serializer_class = TaskUpdateSerializer
    permission_classes = [IsAuthenticated, IsTaskBoardParticipant]

    def patch(self, request, *args, **kwargs):
        """Apply a partial update to the task."""
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Delete the task permanently."""
        return self.destroy(request, *args, **kwargs)


class AssignedTaskListView(generics.ListAPIView):
    """List the tasks the requesting user is assigned to."""

    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Return the tasks where the user is the assignee."""
        return task_queryset().filter(assignee=self.request.user)


class ReviewingTaskListView(generics.ListAPIView):
    """List the tasks the requesting user has to review."""

    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Return the tasks where the user is the reviewer."""
        return task_queryset().filter(reviewer=self.request.user)
