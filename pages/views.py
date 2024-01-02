from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

from pages.forms import PageEditForm
from pages.models import Page
from users.permissions import LoginRequiredMixin, PermissionRequiredMixin


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "pages/home.html"


class PageDetailView(DetailView):
    model = Page
    template_name = "pages/detail.html"


class PageEditView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = PageEditForm
    model = Page
    permissions_formula_GET = [["stranky"]]
    permissions_formula_POST = permissions_formula_GET
    success_message = _("Stránka byla úspěšně upravena.")
    template_name = "pages/edit.html"


class ErrorPage400View(TemplateView):
    template_name = "pages/errors/400.html"


class ErrorPage403View(TemplateView):
    template_name = "pages/errors/403.html"


class ErrorPage404View(TemplateView):
    template_name = "pages/errors/404.html"


class ErrorPage500View(TemplateView):
    template_name = "pages/errors/500.html"
