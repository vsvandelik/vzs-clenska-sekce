from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from persons.models import Person
from vzs import settings

from . import forms
from .backends import GoogleBackend
from .models import Permission, ResetPasswordToken, User
from .permissions import (
    PermissionRequiredMixin,
    UserCreateDeletePermissionMixin,
    UserGeneratePasswordPermissionMixin,
    UserManagePermissionsPermissionMixin,
)
from .utils import get_random_password


class UserCreateView(
    UserCreateDeletePermissionMixin, SuccessMessageMixin, generic.edit.CreateView
):
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

        kwargs["person"] = self.person

        return kwargs

    def get_context_data(self, **kwargs):
        kwargs.setdefault("person", self.person)

        return super().get_context_data(**kwargs)


class UserDeleteView(
    UserCreateDeletePermissionMixin, SuccessMessageMixin, generic.edit.DeleteView
):
    model = User
    context_object_name = "user_object"
    template_name = "users/delete.html"

    def dispatch(self, request, *args, **kwargs):
        self.person = self.get_object().person
        return super().dispatch(request, *args, **kwargs)

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


class UserChangePasswordBaseMixin(generic.edit.UpdateView):
    model = User
    context_object_name = "user_object"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("persons:detail", kwargs={"pk": self.object.pk})

    def get_form_kwargs(self):
        # a weird trick that ensures that the logged in user instance gets the changes
        kwargs = super().get_form_kwargs()

        if self.request.user == self.object:
            kwargs.update({"instance": self.request.user})

        return kwargs

    def form_valid(self, form):
        self.object = form.save()

        update_session_auth_hash(self.request, self.object)

        return generic.edit.FormMixin.form_valid(self, form)


class UserChangePasswordMixin(SuccessMessageMixin, UserChangePasswordBaseMixin):
    pass


class UserChangePasswordBaseMixin(UserChangePasswordMixin):
    template_name = "users/change_password.html"
    success_message = _("Heslo bylo úspěšně změněno.")


class UserChangePasswordSelfView(UserChangePasswordBaseMixin):
    form_class = forms.UserChangePasswordOldAndRepeatForm

    def get_object(self, queryset=None):
        return self.request.active_person.user

    def get_success_url(self):
        return reverse("my-profile:index")


class UserChangePasswordOtherView(PermissionRequiredMixin, UserChangePasswordBaseMixin):
    permissions_required = ["superuser"]
    form_class = forms.UserChangePasswordRepeatForm


class UserGenerateNewPasswordView(
    UserGeneratePasswordPermissionMixin, UserChangePasswordMixin
):
    http_method_names = ["post"]
    form_class = forms.UserChangePasswordForm
    success_message = _("Heslo bylo úspěšně vygenerováno a zasláno osobě e-mailem.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        self.password = get_random_password()

        kwargs["data"] = {"password": self.password}

        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        send_mail(
            _("Vaše heslo bylo změněno"),
            _(f"Vaše heslo bylo změněno administrátorem na {self.password}."),
            None,
            [self.object.person.email],
            fail_silently=False,
        )

        return response


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


class PermissionsView(UserManagePermissionsPermissionMixin, generic.list.ListView):
    model = Permission
    template_name = "users/permissions.html"
    context_object_name = "permissions"


class PermissionDetailView(
    UserManagePermissionsPermissionMixin, generic.detail.DetailView
):
    model = Permission
    template_name = "users/permission_detail.html"


class UserAssignRemovePermissionView(
    UserManagePermissionsPermissionMixin,
    SuccessMessageMixin,
    generic.detail.SingleObjectMixin,
    generic.edit.FormView,
):
    form_class = forms.UserAssignRemovePermissionForm

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=User.objects.all())
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("persons:detail", kwargs={"pk": self.object.person.pk})

    def _change_user_permission(self, user, permission):
        raise ImproperlyConfigured("_change_user_permission needs to be overridden.")

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
    http_method_names = ["get"]
    redirect_field_name = "state"
    next_page = settings.LOGIN_REDIRECT_URL

    def _error(self, request, message):
        messages.error(request, message)
        return redirect("users:login")

    def get(self, request, *args, **kwargs):
        code = request.GET.get("code")

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

        kwargs.setdefault("person", self.object.person)

        return super().get_context_data(**kwargs)

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


class UserResetPasswordRequestView(SuccessMessageMixin, generic.edit.CreateView):
    template_name = "users/reset-password-request.html"
    form_class = forms.UserResetPasswordRequestForm
    success_url = reverse_lazy("users:login")
    success_message = _("E-mail s odkazem pro změnu hesla byl odeslán.")

    def form_valid(self, form):
        response = super().form_valid(form)

        if form.user_found:
            token = self.object

            send_mail(
                _("Zapomenuté heslo"),
                _(
                    f"Nasledujte následující odkaz pro změnu hesla: {settings.SERVER_PROTOCOL}://{settings.SERVER_DOMAIN}{reverse('users:reset-password')}?token={token.key}"
                ),
                None,
                [token.user.person.email],
                fail_silently=False,
            )

        return response


class UserResetPasswordView(SuccessMessageMixin, generic.edit.UpdateView):
    template_name = "users/reset-password.html"
    form_class = forms.UserChangePasswordRepeatForm
    success_url = reverse_lazy("users:login")
    success_message = _("Heslo změněno.")

    def get_object(self, queryset=None):
        token_key = self.request.GET.get("token")

        if token_key is None:
            raise Http404()

        token = get_object_or_404(
            ResetPasswordToken.objects.exclude(ResetPasswordToken.has_expired),
            key=token_key,
        )

        self.token = token

        return token.user

    def form_valid(self, form):
        response = super().form_valid(form)

        self.token.delete()

        return response
