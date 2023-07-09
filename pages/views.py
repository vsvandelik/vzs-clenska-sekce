from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, DetailView, UpdateView

from pages.forms import PageEditForm
from pages.models import Page


class HomeView(TemplateView):
    template_name = "pages/home.html"


class PageDetailView(DetailView):
    template_name = "pages/detail.html"
    model = Page


class PageEditView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = "pages.stranky"
    template_name = "pages/edit.html"
    model = Page
    form_class = PageEditForm
    success_message = _("Stránka byla úspěšně upravena.")


class ErrorPage400View(TemplateView):
    template_name = "pages/errors/400.html"


class ErrorPage403View(TemplateView):
    template_name = "pages/errors/403.html"


class ErrorPage404View(TemplateView):
    template_name = "pages/errors/404.html"


class ErrorPage500View(TemplateView):
    template_name = "pages/errors/500.html"
