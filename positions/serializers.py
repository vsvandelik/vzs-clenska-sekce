from positions.models import EventPosition

from rest_framework.serializers import ModelSerializer


class PositionSerializer(ModelSerializer):
    class Meta:
        model = EventPosition
        fields = "__all__"
