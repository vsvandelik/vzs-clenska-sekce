from .models import EventPosition

from events.models import EventPersonTypeConstraint
from features.models import Feature

from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField


class PositionSerializer(ModelSerializer):
    class Meta:
        model = EventPosition
        fields = "__all__"

    allowed_person_types = PrimaryKeyRelatedField(
        queryset=EventPersonTypeConstraint.objects.all(), many=True
    )

    required_features = PrimaryKeyRelatedField(
        queryset=Feature.objects.all(), many=True
    )
