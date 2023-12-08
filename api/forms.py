from django.forms import ModelForm

from .models import Token


class TokenGenerateForm(ModelForm):
    """
    Form for creating a new API token.

    The ``key`` field is randomly generated.

    See :class:`Token`.

    **Request parameters**:

    *   ``name`` - The name of the token.
    """

    class Meta:
        model = Token
        fields = ["name"]
