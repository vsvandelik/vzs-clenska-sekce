from .models import User

from persons.models import Person

from rest_framework.serializers import (
    HyperlinkedModelSerializer,
    HyperlinkedRelatedField,
)


class UserSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = User
        exclude = ["password"]
        extra_kwargs = {
            "url": {"view_name": "api:user-detail"},
        }

    person = HyperlinkedRelatedField(
        queryset=Person.objects.all(), view_name="api:person-detail"
    )
