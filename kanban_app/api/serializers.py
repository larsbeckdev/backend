"""Serializers for boards, tasks and comments."""

from rest_framework import serializers

from auth_app.api.serializers import UserShortSerializer
from auth_app.models import User

from ..models import Board, Comment, Task
from .permissions import is_board_participant


def validate_board_membership(user, board, field_name):
    """Raise a validation error when a user does not belong to a board."""
    if user is None or is_board_participant(board, user):
        return
    raise serializers.ValidationError(
        {field_name: 'This user is not a member of the board.'})


class TaskSerializer(serializers.ModelSerializer):
    """Full task representation returned by the task endpoints."""

    assignee = UserShortSerializer(read_only=True)
    reviewer = UserShortSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    assignee_id = serializers.PrimaryKeyRelatedField(
        source='assignee', queryset=User.objects.all(),
        write_only=True, required=False, allow_null=True)
    reviewer_id = serializers.PrimaryKeyRelatedField(
        source='reviewer', queryset=User.objects.all(),
        write_only=True, required=False, allow_null=True)

    class Meta:
        model = Task
        fields = ['id', 'board', 'title', 'description', 'status', 'priority',
                  'assignee', 'reviewer', 'due_date', 'comments_count',
                  'assignee_id', 'reviewer_id']

    def get_comments_count(self, obj):
        """Return the annotated comment count or fall back to a query."""
        count = getattr(obj, 'comments_count', None)
        return obj.comments.count() if count is None else count


class BoardTaskSerializer(TaskSerializer):
    """Task representation embedded in the board detail payload."""

    class Meta(TaskSerializer.Meta):
        fields = ['id', 'title', 'description', 'status', 'priority',
                  'assignee', 'reviewer', 'due_date', 'comments_count']


class TaskCreateSerializer(TaskSerializer):
    """Validate a new task against the board resolved by the view."""

    class Meta(TaskSerializer.Meta):
        read_only_fields = ['board']

    def validate(self, attrs):
        """Ensure assignee and reviewer belong to the target board."""
        board = self.context['board']
        validate_board_membership(attrs.get('assignee'), board, 'assignee_id')
        validate_board_membership(attrs.get('reviewer'), board, 'reviewer_id')
        return attrs


class TaskUpdateSerializer(TaskSerializer):
    """Update an existing task without allowing it to change boards."""

    class Meta(TaskSerializer.Meta):
        fields = ['id', 'title', 'description', 'status', 'priority',
                  'assignee', 'reviewer', 'due_date',
                  'assignee_id', 'reviewer_id']

    def validate(self, attrs):
        """Ensure assignee and reviewer still belong to the task's board."""
        board = self.instance.board
        validate_board_membership(attrs.get('assignee'), board, 'assignee_id')
        validate_board_membership(attrs.get('reviewer'), board, 'reviewer_id')
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    """Comment representation with the author rendered as a display name."""

    author = serializers.CharField(source='author.fullname', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']


class BoardSummarySerializer(serializers.ModelSerializer):
    """Board representation used by the list and create endpoints."""

    member_count = serializers.IntegerField(read_only=True)
    ticket_count = serializers.IntegerField(read_only=True)
    tasks_to_do_count = serializers.IntegerField(read_only=True)
    tasks_high_prio_count = serializers.IntegerField(read_only=True)
    owner_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'member_count', 'ticket_count',
                  'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id']


class BoardCreateSerializer(serializers.ModelSerializer):
    """Validate the payload of a new board and attach its members."""

    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False)

    class Meta:
        model = Board
        fields = ['title', 'members']

    def create(self, validated_data):
        """Create the board with the requesting user as its owner."""
        members = validated_data.pop('members', [])
        board = Board.objects.create(
            owner=self.context['request'].user, **validated_data)
        board.members.set(members)
        return board


class BoardDetailSerializer(serializers.ModelSerializer):
    """Board representation including its members and all of its tasks."""

    owner_id = serializers.IntegerField(read_only=True)
    members = UserShortSerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']


class BoardUpdateSerializer(serializers.ModelSerializer):
    """Update the title and the member list of an existing board."""

    owner_data = UserShortSerializer(source='owner', read_only=True)
    members_data = UserShortSerializer(source='members', many=True,
                                       read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False, write_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_data', 'members_data', 'members']

    def update(self, instance, validated_data):
        """Apply the title change and replace the member list when given."""
        members = validated_data.pop('members', None)
        instance.title = validated_data.get('title', instance.title)
        instance.save()
        if members is not None:
            instance.members.set(members)
        return instance
