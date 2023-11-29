from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.core.exceptions import ImproperlyConfigured

from persons.models import get_active_user
from persons.views import PersonPermissionMixin


class PermissionRequiredMixin(DjangoPermissionRequiredMixin):
    """
    Base class for all permission mixins.
    """

    permissions_required = None
    """:meta private:"""

    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, **kwargs):
        """
        Should return ``True`` iff the user is permitted to access the view.

        Default implementation checks if the user has all permissions specified
        in the ``permissions_required`` class variable.

        Override for custom behavior.
        """

        if cls.permissions_required is None:
            raise ImproperlyConfigured(
                f"{cls.__name__} is missing a permissions_required attribute."
            )

        return get_active_user(active_person).has_perms(cls.permissions_required)

    def has_permission(self):
        """
        Hooks into Django's permission system. Do not override or use directly.
        """

        return self.view_has_permission(
            self.request.user, self.request.active_person, **self.kwargs
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
    def view_has_permission(cls, logged_in_user, active_person, pk):
        """:meta private:"""

        person_pk = pk
        return _user_can_manage_person(get_active_user(active_person), person_pk)


class UserGeneratePasswordPermissionMixin(PermissionRequiredMixin):
    """
    Permits superusers and users that manage the given person's membership type
    except for the person's own user account.
    """

    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, pk):
        """:meta private:"""

        person_pk = pk

        # a user shouldn't be allowed to regenerate their own password
        is_different_person = active_person.pk != person_pk

        return is_different_person and _user_can_manage_person(
            get_active_user(active_person), person_pk
        )


class UserManagePermissionsPermissionMixin(PermissionRequiredMixin):
    """
    Permits users with the ``users.spravce_povoleni`` permission.
    """

    permissions_required = ["users.spravce_povoleni"]
    """:meta private:"""
