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


class PageEditView(SuccessMessageMixin, UpdateView):
    template_name = "pages/edit.html"
    model = Page
    form_class = PageEditForm
    success_message = _("Stránka byla úspěšně upravena.")
