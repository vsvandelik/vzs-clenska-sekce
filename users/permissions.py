from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.core.exceptions import ImproperlyConfigured

from persons.views import PersonPermissionMixin


class PermissionRequiredMixin(DjangoPermissionRequiredMixin):
    permissions_required = None

    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, **kwargs):
        if cls.permissions_required is None:
            raise ImproperlyConfigured(
                f"{cls.__name__} is missing a permissions_required attribute."
            )

        return logged_in_user.has_perms(cls.permissions_required)

    def has_permission(self):
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
    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, pk):
        person_pk = pk
        return _user_can_manage_person(logged_in_user, person_pk)


class UserGeneratePasswordPermissionMixin(PermissionRequiredMixin):
    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, pk):
        person_pk = pk

        # a user shouldn't be allowed to regenerate their own password
        is_different_person = logged_in_user.person.pk != person_pk

        return is_different_person and _user_can_manage_person(
            logged_in_user, person_pk
        )


class UserManagePermissionsPermissionMixin(PermissionRequiredMixin):
    permissions_required = ["users.spravce_povoleni"]
