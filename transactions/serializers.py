from .models import Transaction

from events.models import Event

from rest_framework.serializers import (
    HyperlinkedModelSerializer,
    PrimaryKeyRelatedField,
)


class TransactionSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
        extra_kwargs = {
            "url": {"view_name": "api:transaction-detail"},
            "person": {"view_name": "api:person-detail"},
        }

    event = PrimaryKeyRelatedField(queryset=Event.objects.all())
