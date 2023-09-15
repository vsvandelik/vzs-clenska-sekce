from .serializers import (
    PersonSerializer,
    FeatureSerializer,
    GroupSerializer,
    OneTimeEventSerializer,
    TrainingSerializer,
    PositionSerializer,
    TransactionSerializer,
    UserSerializer,
)

from persons.models import Person
from features.models import Feature
from groups.models import Group
from one_time_events.models import OneTimeEvent
from trainings.models import Training
from positions.models import EventPosition
from transactions.models import Transaction
from users.models import User

from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet


class PersonViewSet(ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class FeatureViewSet(ModelViewSet):
    queryset = Feature.qualifications.all()
    serializer_class = FeatureSerializer


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class OneTimeEventViewSet(ModelViewSet):
    queryset = OneTimeEvent.objects.all()
    serializer_class = OneTimeEventSerializer


class TrainingViewSet(ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer


class PositionViewSet(ModelViewSet):
    queryset = EventPosition.objects.all()
    serializer_class = PositionSerializer


class TransactionViewSet(ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
