from functools import reduce

from django.db.models import Q

from persons.models import Person, get_active_user
from users.permissions import PermissionRequiredMixin


class PersonPermissionMixin(PermissionRequiredMixin):
    """
    A mixin for person views' permissions.

    Permits users with one of the following permissions:
    *   "clenska_zakladna"
    *   "detska_clenska_zakladna"
    *   "bazenova_clenska_zakladna"
    *   "lezecka_clenska_zakladna"
    *   "dospela_clenska_zakladna"
    """

    permissions_formula = [
        ["clenska_zakladna"],
        ["detska_clenska_zakladna"],
        ["bazenova_clenska_zakladna"],
        ["lezecka_clenska_zakladna"],
        ["dospela_clenska_zakladna"],
    ]

    @staticmethod
    def get_queryset_by_permission(user, queryset=None):
        """
        Filters all persons or ``queryset`` (if passed) by the ``user``'s permissions.
        """

        if queryset is None:
            queryset = Person.objects.all()

        if user.has_perm("clenska_zakladna"):
            return queryset

        conditions = []

        if user.has_perm("detska_clenska_zakladna"):
            conditions.append(
                Q(person_type__in=[Person.Type.CHILD, Person.Type.PARENT])
            )

        if user.has_perm("bazenova_clenska_zakladna"):
            # TODO: omezit jen na bazenove treninky
            conditions.append(
                Q(person_type__in=[Person.Type.CHILD, Person.Type.PARENT])
            )

        if user.has_perm("lezecka_clenska_zakladna"):
            # TODO: omezit jen na lezecke treninky
            conditions.append(
                Q(person_type__in=[Person.Type.CHILD, Person.Type.PARENT])
            )

        if user.has_perm("dospela_clenska_zakladna"):
            conditions.append(
                Q(
                    person_type__in=[
                        Person.Type.ADULT,
                        Person.Type.EXTERNAL,
                        Person.Type.EXPECTANT,
                        Person.Type.HONORARY,
                        Person.Type.FORMER,
                    ]
                )
            )

        if not conditions:
            return queryset.none()

        return queryset.filter(reduce(lambda x, y: x | y, conditions))

    def _filter_queryset_by_permission(self, queryset=None):
        """:meta private:"""

        return self.get_queryset_by_permission(
            get_active_user(self.request.active_person), queryset
        )

    def _get_available_person_types(self):
        """:meta private:"""

        available_person_types = set()

        active_user = get_active_user(self.request.active_person)

        if active_user.has_perm("clenska_zakladna"):
            available_person_types.update(
                [
                    Person.Type.ADULT,
                    Person.Type.CHILD,
                    Person.Type.EXTERNAL,
                    Person.Type.EXPECTANT,
                    Person.Type.HONORARY,
                    Person.Type.PARENT,
                    Person.Type.FORMER,
                    Person.Type.UNKNOWN,
                ]
            )

        if (
            active_user.has_perm("detska_clenska_zakladna")
            or active_user.has_perm("bazenova_clenska_zakladna")
            or active_user.has_perm("lezecka_clenska_zakladna")
        ):
            available_person_types.update([Person.Type.CHILD, Person.Type.PARENT])

        if active_user.has_perm("dospela_clenska_zakladna"):
            available_person_types.update(
                [
                    Person.Type.ADULT,
                    Person.Type.EXTERNAL,
                    Person.Type.EXPECTANT,
                    Person.Type.HONORARY,
                    Person.Type.FORMER,
                ]
            )

        return list(available_person_types)


class PersonPermissionQuerysetMixin:
    """
    A mixin for person views' permissions.

    Its :func:`get_queryset` filters all persons by the active user's permissions.
    """

    def get_queryset(self):
        """:meta private:"""

        return self._filter_queryset_by_permission()
