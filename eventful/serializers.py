import json
from rest_framework import serializers
from eventful.models import Event


class EventSerializer(serializers.ModelSerializer):

    class Meta:
        model = Event
        fields = ('id', 'event_name', 'webhook', 'max_retry', 'headers')

    def validate_headers(self, value):
        try:
            json.loads(value)
        except Exception:
            raise serializers.ValidationError("Not a valid json")
        return value

    def create(self, validated_data):
        """
        Create an Event object.

        Args:
            validated_data: a DICT contains the Event data after the validation step.

        Returns:
            The created Event object.
        """

        event = Event(**validated_data)
        event.user = self.context['request'].user
        event.save()
        return event
