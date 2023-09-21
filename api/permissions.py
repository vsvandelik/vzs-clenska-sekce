from rest_framework.permissions import BasePermission


class UserPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("api")


class TokenPermission(BasePermission):
    def has_permission(self, request, view):
        return request.auth is not None
