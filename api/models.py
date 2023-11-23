from datetime import datetime

from django.db.models import CharField
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token as BaseToken


class Token(BaseToken):
    """
    Represents a authentication token for the REST API.

    If ``key`` is not set, a random key will be generated on :func:`save`.
    """

    name = CharField(_("Název"), max_length=50)
    """
    The name of the token.
    """

    key: str
    """
    The token value.
    """

    created: datetime
    """
    The date and time when the token was created.
    """

    user = None
    """:meta private:"""

    get_next_by_created: ...
    """:meta private:"""
    get_previous_by_created: ...
    """:meta private:"""
