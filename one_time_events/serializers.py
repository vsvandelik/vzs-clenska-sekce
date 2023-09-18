from one_time_events.models import OneTimeEvent

from rest_framework.serializers import ModelSerializer


class OneTimeEventSerializer(ModelSerializer):
    class Meta:
        model = OneTimeEvent
        fields = "__all__"
