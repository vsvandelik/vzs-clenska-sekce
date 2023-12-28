from rest_framework.permissions import BasePermission

from persons.views import PersonPermissionBaseMixin


class UserPermission(BasePermission):
    """
    Permits users with the `api` permission.
    """

    def has_permission(self, request, view):
        return request.user.has_perm("api")


class TokenPermission(BasePermission):
    """
    Permits only when a valid token is sent in the request header.
    """

    def has_permission(self, request, view):
        return request.auth is not None


class PersonPermission(PersonPermissionBaseMixin, BasePermission):
    """
    Permits users who can manage at least one person membership type.
    """

    def has_permission(self, request, view):
        return self.permission_predicate(request)
