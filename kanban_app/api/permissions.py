"""Object level permissions for the kanban API."""

from rest_framework.permissions import BasePermission


def is_board_participant(board, user):
    """Return whether a user owns the board or is one of its members."""
    return board.owner_id == user.id or board.members.filter(pk=user.id).exists()


class IsBoardParticipant(BasePermission):
    """Allow board access to the owner and to every board member."""

    message = 'You must be the owner or a member of this board.'

    def has_object_permission(self, request, view, obj):
        """Check participation for the board carried by the view."""
        return is_board_participant(obj, request.user)


class IsBoardOwnerOrParticipant(BasePermission):
    """Let participants read and update a board, but only the owner delete it."""

    message = 'You must be the owner or a member of this board.'

    def has_object_permission(self, request, view, obj):
        """Restrict deletion to the owner and everything else to members."""
        if request.method == 'DELETE':
            self.message = 'Only the board owner can delete this board.'
            return obj.owner_id == request.user.id
        return is_board_participant(obj, request.user)
