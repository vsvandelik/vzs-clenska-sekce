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
from django.utils.crypto import get_random_string
from django.core.mail import send_mail

from .backends import GoogleBackend
from persons.models import Person
from .models import User, Permission
from . import forms
from vzs import settings

import string


class UserCreateView(SuccessMessageMixin, generic.edit.CreateView):
    template_name = "users/create.html"
    form_class = forms.UserCreateForm
    queryset = Person.objects.filter(user__isnull=True)

    def get_success_url(self):
        return reverse("persons:detail", kwargs={"pk": self.person.pk})

    def get_success_message(self, cleaned_data):
        return _(f"{self.object} byl úspěšně přidán.")

    def dispatch(self, request, *args, **kwargs):
        self.person = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs.setdefault("person", self.person)

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.setdefault("person", self.person)

        return context


class IndexView(generic.list.ListView):
    model = User
    template_name = "users/index.html"
    context_object_name = "users"


class UserDeleteView(SuccessMessageMixin, generic.edit.DeleteView):
    model = User
    context_object_name = "user_object"
    template_name = "users/delete.html"

    def get_success_url(self):
        return reverse("persons:detail", kwargs={"pk": self.person.pk})

    def form_valid(self, form):
        # success_message is sent after object deletion so we need to save the data
        # we will need later
        self.user_representation = str(self.object)
        self.person = self.object.person
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return _(f"{self.user_representation} byl úspěšně odstraněn.")


class UserChangePasswordView(SuccessMessageMixin, generic.edit.UpdateView):
    model = User
    context_object_name = "user_object"
    template_name = "users/change_password.html"
    form_class = forms.UserChangePasswordForm2
    success_message = _("Heslo bylo úspěšně změněno.")

    def get_success_url(self):
        return reverse("persons:detail", kwargs={"pk": self.object.pk})


class UserGenerateNewPasswordView(SuccessMessageMixin, generic.edit.UpdateView):
    http_method_names = ["post"]
    model = User
    context_object_name = "user_object"
    form_class = forms.UserChangePasswordForm
    success_message = _("Heslo bylo úspěšně vygenerováno a zasláno osobě e-mailem.")

    def get_success_url(self):
        return reverse("persons:detail", kwargs={"pk": self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        self.password = (
            get_random_string(2, string.ascii_uppercase)
            + get_random_string(2, string.ascii_lowercase)
            + get_random_string(4, string.digits)
        )

        kwargs.update({"data": {"password": self.password}})

        return kwargs

    def form_valid(self, form):
        send_mail(
            _("Vaše heslo bylo změněno"),
            _(f"Vaše heslo bylo změněno administrátorem na {self.password}."),
            None,
            [self.object.person.email],
            fail_silently=False,
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        # should not happen
        return super().form_invalid(form)


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
            request.META.get("HTTP_REFERER", reverse_lazy("pages:home"))
        )


class PermissionsView(generic.list.ListView):
    model = Permission
    template_name = "users/permissions.html"
    context_object_name = "permissions"


class PermissionDetailView(generic.detail.DetailView):
    model = Permission
    template_name = "users/permission_detail.html"


class UserAssignRemovePermissionView(
    SuccessMessageMixin, generic.detail.SingleObjectMixin, generic.edit.FormView
):
    form_class = forms.UserAssignRemovePermissionForm

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=User.objects.all())
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("persons:detail", kwargs={"pk": self.object.person.pk})

    def _change_user_permission(self, user, permission):
        pass

    def form_valid(self, form):
        user = self.object
        permission = form.cleaned_data["permission"]

        self._change_user_permission(user, permission)

        return super().form_valid(form)


class GoogleLoginView(generic.base.RedirectView):
    http_method_names = ["post"]

    def get_redirect_url(self, *args, **kwargs):
        next_redirect = self.request.POST.get("next", "")

        return GoogleBackend.get_redirect_url(
            self.request, "users:google-auth", next_redirect
        )


class GoogleAuthView(auth_views.RedirectURLMixin, generic.base.View):
    redirect_field_name = "state"
    next_page = settings.LOGIN_REDIRECT_URL

    def _error(self, request, message):
        messages.error(request, message)
        return redirect("users:login")

    def get(self, request, *args, **kwargs):
        code = request.GET.get("code", "")

        try:
            user = authenticate(request, code=code)
        except User.DoesNotExist:
            return self._error(
                request,
                _(
                    "Přihlášení se nezdařilo, protože osoba s danou e-mailovou adresou nemá založený účet."
                ),
            )
        except Person.DoesNotExist:
            return self._error(
                request,
                _(
                    "Přihlášení se nezdařilo, protože osoba s danou e-mailovou adresou neexistuje."
                ),
            )

        if user is None:
            return self._error(request, _("Přihlášení se nezdařilo."))

        auth_login(request, user)
        set_active_person(request, request.user.person)

        return HttpResponseRedirect(self.get_success_url())

    def get_redirect_url(self):
        return GoogleBackend.state_decode(super().get_redirect_url())


class UserAssignPermissionView(
    generic.list.MultipleObjectMixin, UserAssignRemovePermissionView
):
    template_name = "users/assign_permission.html"
    success_message = _("Povolení úspěšně přidáno.")

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
        return super().get_context_data(**kwargs, person=self.object.person)

    def get_queryset(self):
        # TODO should be:
        # return Permission.objects.difference(self.object.user_permissions.all())
        # but SQlite doesn't support it, change when we start using PostgreSQL
        return Permission.objects.all()

    def _change_user_permission(self, user, permission):
        user.user_permissions.add(permission)


class UserRemovePermissionView(UserAssignRemovePermissionView):
    http_method_names = ["post"]
    success_message = _("Povolení úspěšně odebráno.")

    def _change_user_permission(self, user, permission):
        user.user_permissions.remove(permission)
