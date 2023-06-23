from django.views import generic
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import views as auth_views
from django.contrib.auth import models as auth_models

from .models import User
from . import forms


class CustomCreateMixin(generic.edit.CreateView):
    """
    Allows having multiple additional GET forms in one CreateView
    The purpose is for the GET forms to fill some hidden fields
    of the main POST form of the CreateView
    """

    get_form_classes = []
    default_form_class = None

    def get_initial(self, form_class=None):
        if form_class is None:
            form_class = self.form_class

        return {
            declared_field: self.request.GET.get(declared_field)
            for declared_field in form_class.declared_fields
            if declared_field != "form_id" and declared_field in self.request.GET
        }

    def get_context_data(self, **kwargs):
        form_id = self.request.GET.get("form_id", "")

        if form_id == "" and self.default_form_class is not None:
            form_id = self.default_form_class.name

        for form_class in self.get_form_classes:
            form_name = form_class.name

            if form_id == form_name:
                form = form_class(self.request.GET)
            else:
                form = form_class(initial=self.get_initial(form_class))

            kwargs[form_name] = form

        for form_class in self.get_form_classes:
            form_name = form_class.name
            kwargs[form_name].handle(self.request, kwargs)

        return super().get_context_data(**kwargs)


class UserCreateView(SuccessMessageMixin, CustomCreateMixin):
    template_name = "users/create.html"
    form_class = forms.UserCreateForm
    success_url = reverse_lazy("users:add")
    get_form_classes = [forms.PersonSearchForm, forms.PersonSelectForm]
    default_form_class = forms.PersonSearchForm

    def get_success_message(self, cleaned_data):
        return _(f"{self.object} byl úspěšně přidán.")


class IndexView(generic.list.ListView):
    template_name = "users/index.html"
    context_object_name = "users"
    paginate_by = 8

    def get_queryset(self):
        self.user_search_form = forms.UserSearchForm(self.request.GET)
        self.user_search_pagination_form = forms.UserSearchPaginationForm(
            self.request.GET
        )
        return self.user_search_form.search_users()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "user_search_form" not in context:
            context["user_search_form"] = self.user_search_form

        if "user_search_pagination_form" not in context:
            context["user_search_pagination_form"] = self.user_search_pagination_form

        return context


class DetailView(generic.detail.DetailView):
    model = User
    template_name = "users/detail.html"


class UserDeleteView(SuccessMessageMixin, generic.edit.DeleteView):
    model = User
    template_name = "users/delete.html"
    success_url = reverse_lazy("users:index")

    def form_valid(self, form):
        # success_message is sent after object deletion so we need to save the string
        self.user_representation = str(self.object)
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return _(f"{self.user_representation} byl úspěšně odstraněn.")


class UserEditView(SuccessMessageMixin, generic.edit.UpdateView):
    model = User
    template_name = "users/edit.html"
    form_class = forms.UserEditForm
    success_message = _("Uživatel byl úspěšně upraven.")

    def get_success_url(self):
        return reverse_lazy("users:detail", kwargs={"pk": self.object.pk})


class LoginView(auth_views.LoginView):
    template_name = "users/login.html"
    authentication_form = forms.LoginForm
    redirect_authenticated_user = True


class PermissionsView(generic.list.ListView):
    model = auth_models.Permission
    template_name = "users/permissions.html"
    context_object_name = "permissions"
