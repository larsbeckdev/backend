"""Serializers for boards, tasks and comments."""

from rest_framework import serializers

from auth_app.api.serializers import UserShortSerializer
from auth_app.models import User

from ..models import Board


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
