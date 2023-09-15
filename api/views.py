from .models import Token
from .forms import TokenGenerateForm

from users.views import PermissionRequiredMixin

from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, DeleteView
from django.urls import reverse_lazy


class APIPermissionRequiredMixin(PermissionRequiredMixin):
    permission_required = "api"


class TokenIndexView(APIPermissionRequiredMixin, ListView):
    model = Token
    template_name = "api/token/index.html"
    context_object_name = "tokens"


class TokenDeleteView(APIPermissionRequiredMixin, DeleteView):
    model = Token
    template_name = "api/token/delete.html"
    success_url = reverse_lazy("api:token-index")


class TokenGenerateView(APIPermissionRequiredMixin, CreateView):
    template_name = "api/token/generate.html"
    form_class = TokenGenerateForm

    def form_valid(self, form):
        form.save()
        return self.render_to_response(
            self.get_context_data(token_key=form.instance.key)
        )
