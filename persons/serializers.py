from rest_framework.serializers import (
    HyperlinkedModelSerializer,
    HyperlinkedRelatedField,
)

from features.models import Feature

from .models import Person


class PersonSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Person
        fields = "__all__"
        extra_kwargs = {
            "url": {"view_name": "api:person-detail"},
        }

    managed_persons = HyperlinkedRelatedField(
        queryset=Person.objects.all(),
        many=True,
        view_name="api:person-detail",
    )

    features = HyperlinkedRelatedField(
        queryset=Feature.objects.all(),
        many=True,
        view_name="api:feature-detail",
    )
