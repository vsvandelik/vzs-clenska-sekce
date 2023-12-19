from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
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
from vzs.utils import filter_queryset

from .permissions import PersonPermission, TokenPermission, UserPermission
from .utils import PersonExistsFilter


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


class PersonExistsView(APIView):
    """
    Checks if there are any persons matching the filter :class:`PersonAPIFilter`.

    Filter gets its parameters from the query parameters.

    **Query parameters:**

    *   ``first_name`` - First name of the person.
    *   ``last_name`` - Last name of the person.
    """

    permission_classes = [IsAuthenticated & PersonPermission]
    """:meta private:"""

    def post(self, request, format=None):
        """:meta private:"""

        does_exist = filter_queryset(
            Person.objects, request.data, PersonExistsFilter
        ).exists()

        return Response(does_exist)


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
