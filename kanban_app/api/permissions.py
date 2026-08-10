"""Object level permissions for the kanban API."""

from rest_framework.permissions import BasePermission


def is_board_participant(board, user):
    """Return whether a user owns the board or is one of its members."""
    return board.owner_id == user.id or board.members.filter(pk=user.id).exists()


class IsBoardOwnerOrParticipant(BasePermission):
    """Let participants read and update a board, but only the owner delete it."""

    message = 'You must be the owner or a member of this board.'

    def has_object_permission(self, request, view, obj):
        """Restrict deletion to the owner and everything else to members."""
        if request.method == 'DELETE':
            self.message = 'Only the board owner can delete this board.'
            return obj.owner_id == request.user.id
        return is_board_participant(obj, request.user)


class IsTaskBoardParticipant(BasePermission):
    """Let board members edit a task, but restrict deletion further.

    Only the user who created the task or the owner of its board may
    delete it, as required by the API documentation.
    """

    message = 'You must be a member of the board this task belongs to.'

    def has_object_permission(self, request, view, obj):
        """Check membership for updates and ownership for deletions."""
        if request.method == 'DELETE':
            self.message = ('Only the task creator or the board owner can '
                            'delete this task.')
            return (obj.created_by_id == request.user.id
                    or obj.board.owner_id == request.user.id)
        return is_board_participant(obj.board, request.user)


class IsCommentAuthor(BasePermission):
    """Allow only the author of a comment to delete it."""

    message = 'Only the author of this comment can delete it.'

    def has_object_permission(self, request, view, obj):
        """Compare the comment author with the requesting user."""
        return obj.author_id == request.user.id
