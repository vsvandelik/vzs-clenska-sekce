from .models import Token

from django.utils.translation import gettext_lazy as _

from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication
from rest_framework import exceptions


class TokenAuthentication(BaseTokenAuthentication):
    def authenticate_credentials(self, key):
        try:
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("Invalid token."))

        return (None, token)
