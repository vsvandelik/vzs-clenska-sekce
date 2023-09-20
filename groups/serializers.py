from .models import Group

from persons.models import Person

from rest_framework.serializers import (
    HyperlinkedModelSerializer,
    HyperlinkedRelatedField,
)


class GroupSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"
        extra_kwargs = {
            "url": {"view_name": "api:group-detail"},
        }

    members = HyperlinkedRelatedField(
        queryset=Person.objects.all(),
        many=True,
        view_name="api:person-detail",
    )
