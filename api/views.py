from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.list import ListView

from users.views import PermissionRequiredMixin

from .forms import TokenGenerateForm
from .models import Token


class APIPermissionRequiredMixin(PermissionRequiredMixin):
    permissions_required = ["api"]


class TokenIndexView(APIPermissionRequiredMixin, ListView):
    model = Token
    template_name = "api/token/index.html"
    context_object_name = "tokens"


class TokenDeleteView(APIPermissionRequiredMixin, DeleteView):
    model = Token
    template_name = "api/token/delete.html"
    success_url = reverse_lazy("api:token:index")


class TokenGenerateView(APIPermissionRequiredMixin, CreateView):
    template_name = "api/token/generate.html"
    form_class = TokenGenerateForm
    success_url = reverse_lazy("api:token:index")
