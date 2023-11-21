from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.list import ListView

from users.views import PermissionRequiredMixin

from .forms import TokenGenerateForm
from .models import Token


class APIPermissionRequiredMixin(PermissionRequiredMixin):
    """
    Permits users with the ``api`` permission.
    """

    permissions_required = ["api"]
    """:meta private:"""


class TokenIndexView(APIPermissionRequiredMixin, ListView):
    """
    Displays a list of all :class:`api.models.Token`.

    **Permissions**:

    Users with the ``api`` permission.
    """

    model = Token
    """:meta private:"""

    template_name = "api/token/index.html"
    """:meta private:"""

    context_object_name = "tokens"
    """:meta private:"""


class TokenDeleteView(APIPermissionRequiredMixin, DeleteView):
    """
    Deletes a :class:`api.models.Token`.

    **Success redirection view**: :class:`api.views.TokenIndexView`

    **Permissions**:

    Users with the ``api`` permission.

    **Path parameters**:

    *   ``pk`` - The key of the :class:`api.models.Token` to be deleted.
    """

    model = Token
    """:meta private:"""

    template_name = "api/token/delete.html"
    """:meta private:"""

    success_url = reverse_lazy("api:token:index")
    """:meta private:"""


class TokenGenerateView(APIPermissionRequiredMixin, CreateView):
    """
    Generates a new :class:`api.models.Token`.

    **Success redirection view**: :class:`api.views.TokenIndexView`

    **Permissions**:

    Users with the ``api`` permission.
    """

    template_name = "api/token/generate.html"
    """:meta private:"""

    form_class = TokenGenerateForm
    """:meta private:"""

    success_url = reverse_lazy("api:token:index")
    """:meta private:"""
