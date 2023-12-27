from collections.abc import Collection, Iterable

from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)

from persons.models import get_active_user
from persons.views import PersonPermissionMixin


class PermissionRequiredMixin(DjangoPermissionRequiredMixin):
    """
    Base class for all permission mixins.
    """

    permissions_formula: Iterable[Collection[str]]
    """
    A DNF formula of required permissions.
    """

    @classmethod
    def view_has_permission_person(cls, active_person, **kwargs):
        """
        :meta private:
        """

        active_user = get_active_user(active_person)
        return cls.view_has_permission(active_user, **kwargs)

    @classmethod
    def view_has_permission(cls, active_user, **kwargs):
        """
        Should return ``True`` iff the user is permitted to access the view.

        Default implementation checks if the active user's permissions satisfy
        `permissions_formula`.

        Override for custom behavior.
        """

        return any(
            active_user.has_perms(conjunction)
            for conjunction in cls.permissions_formula
        )

    def has_permission(self):
        """
        Hooks into Django's permission system. Do not override or use directly.
        """

        return self.view_has_permission_person(
            self.request.active_person, **self.kwargs
        )


def _user_can_manage_person(user, person_pk):
    return user.is_superuser or (
        PersonPermissionMixin.get_queryset_by_permission(user)
        .filter(pk=person_pk)
        .exists()
    )


class UserCreateDeletePermissionMixin(PermissionRequiredMixin):
    """
    Permits superusers and users that manage the given person's membership type.
    """

    @classmethod
    def view_has_permission(cls, active_user, pk):
        """:meta private:"""

        person_pk = pk
        return _user_can_manage_person(active_user, person_pk)


class UserGeneratePasswordPermissionMixin(PermissionRequiredMixin):
    """
    Permits superusers and users that manage the given person's membership type
    except for the person's own user account.
    """

    @classmethod
    def view_has_permission(cls, active_user, pk):
        """:meta private:"""

        person_pk = pk

        # a user shouldn't be allowed to regenerate their own password
        is_different_person = active_user.person.pk != person_pk

        return is_different_person and _user_can_manage_person(active_user, person_pk)


class UserManagePermissionsPermissionMixin(PermissionRequiredMixin):
    """
    Permits users with the ``users.povoleni`` permission.
    """

    permissions_formula = [["povoleni"]]
    """:meta private:"""
