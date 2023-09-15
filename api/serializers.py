from persons.models import Person
from features.models import Feature
from groups.models import Group
from one_time_events.models import OneTimeEvent
from trainings.models import Training
from positions.models import EventPosition
from transactions.models import Transaction
from users.models import User

from rest_framework.serializers import ModelSerializer


class PersonSerializer(ModelSerializer):
    class Meta:
        model = Person
        fields = "__all__"


class FeatureSerializer(ModelSerializer):
    class Meta:
        model = Feature
        fields = "__all__"


class GroupSerializer(ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class OneTimeEventSerializer(ModelSerializer):
    class Meta:
        model = OneTimeEvent
        fields = "__all__"


class TrainingSerializer(ModelSerializer):
    class Meta:
        model = Training
        fields = "__all__"


class PositionSerializer(ModelSerializer):
    class Meta:
        model = EventPosition
        fields = "__all__"


class TransactionSerializer(ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        exclude = ["password"]
