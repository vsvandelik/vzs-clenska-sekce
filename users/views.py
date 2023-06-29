from django.views import generic
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import views as auth_views
from django.contrib.auth import models as auth_models
from django.utils.functional import SimpleLazyObject
from django.http import (
    HttpResponseRedirect,
    HttpResponseForbidden,
    HttpResponseBadRequest,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist

from .backends import GoogleBackend
from persons.models import Person
from .models import User, Permission
from . import forms
from persons.models import Person


class UserCreateView(SuccessMessageMixin, generic.edit.CreateView):
    template_name = "users/create.html"
    form_class = forms.UserCreateForm
    success_url = reverse_lazy("users:add")

    def get_success_message(self, cleaned_data):
        return _(f"{self.object} byl úspěšně přidán.")

    def get_initial(self):
        return {"person": self.request.GET.get("person")}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "people" not in context:
            context["people"] = Person.objects.filter(user__isnull=True)

        if "user_create_form" not in context:
            context["user_create_form"] = context["form"]

        if "person_select_form" not in context:
            context["person_select_form"] = forms.PersonSelectForm(self.request.GET)

        return context


class IndexView(generic.list.ListView):
    model = User
    template_name = "users/index.html"
    context_object_name = "users"


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


def set_active_person(request, person):
    request.session["_active_person_pk"] = person.pk


class LoginView(auth_views.LoginView):
    template_name = "users/login.html"
    authentication_form = forms.LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)

        set_active_person(self.request, self.request.user.person)

        return response


class ChangeActivePersonView(LoginRequiredMixin, generic.edit.BaseFormView):
    http_method_names = ["post"]
    form_class = forms.ChangeActivePersonForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        request = self.request
        user = request.user

        new_active_person = form.cleaned_data["person"]

        if new_active_person in user.person.get_managed_persons():
            set_active_person(request, new_active_person)
            messages.success(request, _("Aktivní osoba úspěšně změněna."))
        else:
            return HttpResponseForbidden(
                _("Vybraná osoba není spravována přihlášenou osobou.")
            )

        return HttpResponseRedirect(
            request.META.get("HTTP_REFERER", reverse_lazy("persons:index"))
        )


class PermissionsView(generic.list.ListView):
    model = Permission
    template_name = "users/permissions.html"
    context_object_name = "permissions"


class PermissionDetailView(generic.detail.DetailView):
    model = Permission
    template_name = "users/permission_detail.html"


class PermissionAssignView(
    generic.detail.SingleObjectTemplateResponseMixin,
    generic.detail.SingleObjectMixin,
    generic.edit.BaseFormView,
):
    http_method_names = ["post"]
    form_class = forms.PermissionAssignForm
    model = User

    def get_success_url(self):
        return reverse_lazy("users:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        self.object = self.get_object()

        user = self.object
        permission = form.cleaned_data["permission"]

        user.user_permissions.add(permission)

        return super().form_valid(form)


class GoogleLoginView(generic.base.RedirectView):
    http_method_names = ["post"]

    def get_redirect_url(self, *args, **kwargs):
        return GoogleBackend.get_redirect_url(self.request, "users:google-auth")


class GoogleAuthView(generic.base.View):
    def get(self, request, *args, **kwargs):
        code = request.GET.get("code", "")

        try:
            user = authenticate(request, code=code)
        except ObjectDoesNotExist:
            messages.error(
                request,
                _(
                    "Přihlášení se nezdařilo, protože e-mailová adresa Google účtu není v systému registrovaná."
                ),
            )
            return redirect("users:login")

        if user is None:
            messages.error(request, _("Přihlášení se nezdařilo."))
            return redirect("users:login")

        auth_login(request, user)
        set_active_person(request, request.user.person)

        return redirect("persons:detail", pk=request.user.person.pk)
