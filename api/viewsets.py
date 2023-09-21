from .permissions import UserPermission, TokenPermission

from persons.serializers import PersonSerializer
from features.serializers import FeatureSerializer
from groups.serializers import GroupSerializer
from one_time_events.serializers import OneTimeEventSerializer
from trainings.serializers import TrainingSerializer
from positions.serializers import PositionSerializer
from transactions.serializers import TransactionSerializer
from users.serializers import UserSerializer

from persons.models import Person
from features.models import Feature
from groups.models import Group
from one_time_events.models import OneTimeEvent
from trainings.models import Training
from positions.models import EventPosition
from transactions.models import Transaction
from users.models import User

from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated


class APIPermissionMixin:
    permission_classes = [(IsAuthenticated & UserPermission) | TokenPermission]


class PersonViewSet(APIPermissionMixin, ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class FeatureViewSet(APIPermissionMixin, ModelViewSet):
    queryset = Feature.qualifications.all()
    serializer_class = FeatureSerializer


class GroupViewSet(APIPermissionMixin, ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class OneTimeEventViewSet(APIPermissionMixin, ModelViewSet):
    queryset = OneTimeEvent.objects.all()
    serializer_class = OneTimeEventSerializer


class TrainingViewSet(APIPermissionMixin, ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer


class PositionViewSet(APIPermissionMixin, ModelViewSet):
    queryset = EventPosition.objects.all()
    serializer_class = PositionSerializer


class TransactionViewSet(APIPermissionMixin, ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class UserViewSet(APIPermissionMixin, ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
