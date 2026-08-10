"""API views for boards, tasks and comments."""

from rest_framework import generics, status
from rest_framework.response import Response

from ..models import Board
from .serializers import BoardCreateSerializer, BoardSummarySerializer
from .utils import boards_for_user


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
