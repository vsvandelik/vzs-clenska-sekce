from .models import OneTimeEvent

from events.models import EventPersonTypeConstraint

from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField


class OneTimeEventSerializer(ModelSerializer):
    class Meta:
        model = OneTimeEvent
        exclude = ["polymorphic_ctype"]

    allowed_person_types = PrimaryKeyRelatedField(
        queryset=EventPersonTypeConstraint.objects.all(), many=True
    )
