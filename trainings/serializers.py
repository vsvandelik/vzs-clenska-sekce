from .models import Training

from events.models import EventPersonTypeConstraint

from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField


class TrainingSerializer(ModelSerializer):
    class Meta:
        model = Training
        exclude = ["polymorphic_ctype"]

    allowed_person_types = PrimaryKeyRelatedField(
        queryset=EventPersonTypeConstraint.objects.all(), many=True
    )
