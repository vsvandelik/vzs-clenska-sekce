from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, DetailView, UpdateView

from pages.forms import PageEditForm
from pages.models import Page
from vzs import settings


class HomeView(TemplateView):
    template_name = "pages/home.html"


class PageDetailView(DetailView):
    template_name = "pages/detail.html"
    model = Page


class PageEditView(SuccessMessageMixin, UpdateView):
    template_name = "pages/edit.html"
    model = Page
    form_class = PageEditForm
    success_message = _("Stránka byla úspěšně upravena.")


class ErrorPageMixin(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["admin_email"] = settings.ADMIN_EMAIL
        return context


class ErrorPage400View(ErrorPageMixin):
    template_name = "pages/errors/400.html"


class ErrorPage403View(ErrorPageMixin):
    template_name = "pages/errors/403.html"


class ErrorPage404View(ErrorPageMixin):
    template_name = "pages/errors/404.html"


class ErrorPage500View(ErrorPageMixin):
    template_name = "pages/errors/500.html"
