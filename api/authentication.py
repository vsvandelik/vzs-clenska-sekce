from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication

from .models import Token


class TokenAuthentication(BaseTokenAuthentication):
    """
    Authenticates against the :class:`api.models.Token` model.
    """

    def authenticate_credentials(self, key: str) -> tuple[None, Token]:
        """
        Looks for a API token with value ``key``.
        """

        try:
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("Invalid token."))

        return (None, token)
