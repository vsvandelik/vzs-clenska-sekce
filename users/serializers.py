from rest_framework.serializers import (
    HyperlinkedModelSerializer,
    HyperlinkedRelatedField,
)

from persons.models import Person

from .models import User


class UserSerializer(HyperlinkedModelSerializer):
    """
    Provides serialization for the :class:`User` model.
    """

    class Meta:
        model = User
        exclude = ["password"]
        extra_kwargs = {
            "url": {"view_name": "api:user-detail"},
        }

    person = HyperlinkedRelatedField(
        queryset=Person.objects.all(), view_name="api:person-detail"
    )
