from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from features.models import Feature
from features.serializers import FeatureSerializer
from groups.models import Group
from groups.serializers import GroupSerializer
from one_time_events.models import OneTimeEvent
from one_time_events.serializers import OneTimeEventSerializer
from persons.models import Person
from persons.serializers import PersonSerializer
from positions.models import EventPosition
from positions.serializers import PositionSerializer
from trainings.models import Training
from trainings.serializers import TrainingSerializer
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer
from users.models import User
from users.serializers import UserSerializer

from .permissions import TokenPermission, UserPermission


class APIPermissionMixin:
    """
    Permits users with the ``api`` permission
    and requests with a valid token in the header.
    """

    permission_classes = [(IsAuthenticated & UserPermission) | TokenPermission]
    """:meta private:"""


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
