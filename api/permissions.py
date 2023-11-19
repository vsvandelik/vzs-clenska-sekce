from rest_framework.permissions import BasePermission


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
