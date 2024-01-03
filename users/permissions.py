from collections.abc import Collection, Iterable

from django.contrib.auth.mixins import LoginRequiredMixin as DjangoLoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.core.exceptions import ImproperlyConfigured

from persons.models import Person, get_active_user


class PermissionRequiredMixin(DjangoPermissionRequiredMixin):
    """
    Base class for all permission mixins.
    """

    permissions_formula: Iterable[Collection[str]] | None = None
    """
    A DNF formula of required permissions for any request.
    """

    permissions_formula_GET: Iterable[Collection[str]] | None = None
    """
    A DNF formula of required permissions for a GET request. Takes precedence over
    ``permissions_formula`` if overridden.
    """

    permissions_formula_POST: Iterable[Collection[str]] | None = None
    """
    A DNF formula of required permissions for a POST request. Takes precedence over
    ``permissions_formula`` if overridden.
    """

    @classmethod
    def view_has_permission_person(cls, method: str, active_person: Person, **kwargs):
        """
        :meta private:
        """

        active_user = get_active_user(active_person)
        return cls.view_has_permission(method, active_user, **kwargs)

    @classmethod
    def view_has_permission(cls, method: str, active_user, **kwargs):
        """
        Should return ``True`` iff the user is permitted to access the view.

        Default implementation checks if the active user's permissions satisfy
        ``permissions_formula`` or ``permissions_formula_POST``
        and ``permissions_formula_GET`` if defined, based on the method, respectively.

        Override for custom behavior.
        """

        formula = getattr(cls, f"permissions_formula_{method}", None)

        if formula is None:
            formula = getattr(cls, "permissions_formula", None)

        if formula is None:
            raise ImproperlyConfigured(
                f"permissions_formula or permissions_formula_{method} "
                f"is not defined on {cls.__name__}"
            )

        return any(active_user.has_perms(conjunction) for conjunction in formula)

    def has_permission(self):
        """
        Hooks into Django's permission system. Do not override or use directly.
        """
        request = self.request
        method = request.method

        return self.view_has_permission_person(
            method,
            request.active_person,
            GET=request.GET,
            POST=request.POST if method == "POST" else {},
            **self.kwargs,
        )


class LoginRequiredMixin(PermissionRequiredMixin):
    @classmethod
    def view_has_permission(cls, method, active_user, **kwargs):
        """
        Should return ``True`` iff the user is logged in.

        Override for custom behavior.
        """

        return active_user.is_authenticated


def _user_can_manage_person(user, person_pk):
    from persons.views import PersonPermissionMixin

    return user.is_superuser or (
        PersonPermissionMixin.get_queryset_by_permission(user)
        .filter(pk=person_pk)
        .exists()
    )


class UserCreateDeletePasswordPermissionMixin(PermissionRequiredMixin):
    """
    Permits superusers and users that manage the given person's membership type.
    """

    @classmethod
    def view_has_permission(cls, method: str, active_user, pk, **kwargs):
        """:meta private:"""

        person_pk = pk
        return _user_can_manage_person(active_user, person_pk)


class UserGeneratePasswordPermissionMixin(PermissionRequiredMixin):
    """
    Permits superusers and users that manage the given person's membership type
    except for the person's own user account.
    """

    @classmethod
    def view_has_permission(cls, method: str, active_user, pk, **kwargs):
        """:meta private:"""

        person_pk = pk

        # a user shouldn't be allowed to regenerate their own password
        is_different_person = active_user.person.pk != person_pk

        return is_different_person and _user_can_manage_person(active_user, person_pk)


class UserManagePermissionsPermissionMixin(PermissionRequiredMixin):
    """
    Permits users with the ``povoleni`` permission.
    """

    permissions_formula = [["povoleni"]]
    """:meta private:"""
