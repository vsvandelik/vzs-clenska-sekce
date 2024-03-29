from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.contrib.auth.views import RedirectURLMixin
from django.contrib.messages import error as error_message
from django.contrib.messages import success as success_message
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import RedirectView, View
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import (
    BaseFormView,
    CreateView,
    DeleteView,
    FormMixin,
    FormView,
    UpdateView,
)
from django.views.generic.list import ListView, MultipleObjectMixin

from persons.models import Person
from vzs.settings import LOGIN_REDIRECT_URL, SERVER_DOMAIN, SERVER_PROTOCOL
from vzs.utils import send_mail

from .backends import GoogleBackend
from .forms import (
    ChangeActivePersonForm,
    LoginForm,
    LogoutForm,
    UserAssignRemovePermissionForm,
    UserChangePasswordForm,
    UserChangePasswordOldAndRepeatForm,
    UserChangePasswordRepeatForm,
    UserDeletePasswordForm,
    UserResetPasswordRequestForm,
)
from .models import Permission, ResetPasswordToken, User
from .permissions import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserCreateDeletePasswordPermissionMixin,
    UserGeneratePasswordPermissionMixin,
    UserManagePermissionsPermissionMixin,
)
from .utils import create_random_password


class UserChangePasswordBaseMixin(UpdateView):
    """
    A base view for changing an existing user's password.

    Logs out the user whose password changed.

    **Success redirection view**: :class:`persons.views.PersonDetailView` of the person
    whose user account's password was changed.
    """

    context_object_name = "user_object"
    """:meta private:"""

    model = User
    """:meta private:"""

    def dispatch(self, request, *args, **kwargs):
        """:meta private:"""

        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """:meta private:"""

        return reverse("persons:detail", kwargs={"pk": self.object.pk})

    def get_form_kwargs(self):
        """:meta private:"""

        # a weird trick that ensures that the logged in user instance gets the changes
        kwargs = super().get_form_kwargs()

        if self.request.user == self.object:
            kwargs.update({"instance": self.request.user})

        return kwargs

    def form_valid(self, form):
        """:meta private:"""

        self.object = form.save()

        update_session_auth_hash(self.request, self.object)

        return FormMixin.form_valid(self, form)


class UserChangePasswordMixin(SuccessMessageMixin, UserChangePasswordBaseMixin):
    """:meta private:"""

    success_message = _("Heslo bylo úspěšně změněno.")
    template_name = "users/change_password.html"


class UserChangePasswordSelfView(LoginRequiredMixin, UserChangePasswordMixin):
    """
    Changes the password of the currently logged in user.

    **Success redirection view**: :class:`persons.views.MyProfileView`

    **Request body parameters**:

    *   ``password``
    *   ``password_repeat`` - For validation purposes only.
    *   ``password_old`` - For validation purposes only.
    """

    form_class = UserChangePasswordOldAndRepeatForm

    def get_object(self, queryset=None):
        """:meta private:"""

        return self.request.active_person.user

    def get_success_url(self):
        """:meta private:"""

        return reverse("my-profile:index")


class UserChangePasswordOtherView(PermissionRequiredMixin, UserChangePasswordMixin):
    """
    Changes password of other users.

    **Success redirection view**: :class:`persons.views.PersonDetailView` of the person
    whose user account's password was changed.

    **Permissions**:

    Superusers.

    **Request body parameters**:

    *   ``password``
    *   ``password_repeat`` - For validation purposes only.

    **Path parameters**:

    *   ``pk`` - The ID of the person whose account password should be changed.
    """

    form_class = UserChangePasswordRepeatForm
    """:meta private:"""

    permissions_formula = [["superuser"]]
    """:meta private:"""


class UserGenerateNewPasswordView(
    UserGeneratePasswordPermissionMixin,
    SuccessMessageMixin,
    UserChangePasswordBaseMixin,
):
    """
    Generates a new random password for a user.

    Sends an email with the new password to the person.

    **Success redirection view**: :class:`persons.views.PersonDetailView` of the person
    whose user account's password was changed.

    **Permissions**:

    Users that can manage the person's membership type except the edited user.

    **Path parameters**:

    *   ``pk`` - The ID of the person whose account password should be changed.
    """

    form_class = UserChangePasswordForm
    """:meta private:"""

    http_method_names = ["post"]
    """:meta private:"""

    success_message = _("Heslo bylo úspěšně vygenerováno a zasláno osobě e-mailem.")
    """:meta private:"""

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()

        self.password = create_random_password()

        kwargs["data"] = {"password": self.password}

        return kwargs

    def form_valid(self, form):
        """:meta private:"""

        response = super().form_valid(form)

        send_mail(
            subject="Vaše heslo bylo změněno",
            message=_(f"Vaše heslo bylo změněno administrátorem na {self.password}."),
            recipient_list=[self.object.person.email],
        )

        return response


def set_active_person(request, person):
    """
    Sets the active person in the session.
    """

    request.session["_active_person_pk"] = person.pk


class LoginView(BaseLoginView):
    """
    Logs in users.

    Also sets the active person to the owner of the user account.

    **Request body parameters**:

    *   ``email``
    *   ``password``
    """

    authentication_form = LoginForm
    """:meta private:"""

    redirect_authenticated_user = True
    """:meta private:"""

    template_name = "users/login.html"
    """:meta private:"""

    def form_valid(self, form):
        """:meta private:"""

        response = super().form_valid(form)

        set_active_person(self.request, self.request.user.person)

        return response


class ChangeActivePersonView(LoginRequiredMixin, BaseFormView):
    """
    Changes the active person.

    **Success redirection view**: The page from which the request originated.

    **Permissions**:

    Logged in users changing to a person they manage.

    **Request body parameters**:

    *   ``person``: The ID of the person to be set as the active person.
    """

    form_class = ChangeActivePersonForm
    """:meta private:"""

    http_method_names = ["post"]
    """:meta private:"""

    def form_valid(self, form):
        """:meta private:"""

        request = self.request
        user = request.user

        new_active_person = form.cleaned_data["person"]

        if new_active_person in user.person.get_managed_persons():
            set_active_person(request, new_active_person)
            success_message(request, _("Aktivní osoba úspěšně změněna."))
        else:
            raise PermissionDenied(
                _("Vybraná osoba není spravována přihlášenou osobou.")
            )

        return HttpResponseRedirect(
            request.META.get("HTTP_REFERER", reverse_lazy("pages:home"))
        )


class PermissionsView(UserManagePermissionsPermissionMixin, ListView):
    """
    Displays all permissions.

    **Permissions**:

    Users with the ``povoleni`` permission.
    """

    context_object_name = "permissions"
    """:meta private:"""

    model = Permission
    """:meta private:"""

    template_name = "users/permissions.html"
    """:meta private:"""


class PermissionDetailView(UserManagePermissionsPermissionMixin, DetailView):
    """
    A view for displaying a permission detail.

    **Permissions**:

    Users with the ``povoleni`` permission.

    **Path parameters**:

    *   ``pk``: The ID of the permission to be displayed.
    """

    model = Permission
    """:meta private:"""

    template_name = "users/permission_detail.html"
    """:meta private:"""


class UserAssignRemovePermissionView(
    UserManagePermissionsPermissionMixin,
    SuccessMessageMixin,
    SingleObjectMixin,
    FormView,
):
    """
    A base view for assigning or removing a permission from a user.

    **Success redirection view**: :class:`persons.views.PersonDetailView` of the person
    whose user account's permissions were changed.

    **Permissions**:

    Users with the ``povoleni`` permission.

    **Request body parameters**:

    *   ``permission``: The ID of the permission to be assigned or removed.

    **Path parameters**:

    *   ``pk``: The ID of the person whose account's permissions should be changed.
    """

    form_class = UserAssignRemovePermissionForm
    """:meta private:"""

    def dispatch(self, request, *args, **kwargs):
        """:meta private:"""

        self.object = self.get_object(queryset=User.objects.all())
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """:meta private:"""

        return reverse("persons:detail", kwargs={"pk": self.object.person.pk})

    @staticmethod
    def change_user_permission(user, permission):
        """
        Callback to handle permission assignment change.
        """

        raise ImproperlyConfigured("_change_user_permission needs to be overridden.")

    def form_valid(self, form):
        """:meta private:"""

        user = self.object
        permission = form.cleaned_data["permission"]

        self.change_user_permission(user, permission)

        return super().form_valid(form)


class GoogleLoginView(RedirectView):
    """
    Google authentication entry view.

    The Google authentication redirection callback is :class:`GoogleAuthView`.
    It is passed the ``next`` request body parameter.

    **Success redirection view**: Google authentication page.

    **Request body parameters**:

    *   ``next``: The final URL to redirect to after successful authentication.
    """

    http_method_names = ["post"]
    """:meta private:"""

    def get_redirect_url(self, *args, **kwargs):
        """:meta private:"""

        next_redirect = self.request.POST.get("next", "")

        return GoogleBackend.create_redirect_url(
            self.request, "users:google-auth", next_redirect
        )


class GoogleAuthView(RedirectURLMixin, View):
    """
    Serves as Google authentication callback.

    Authenticates the user, logs them in and redirects to the final URL.

    **Success redirection view**: The URL passed in the ``state`` query parameter.

    **Query parameters**:

    *   ``code``: The authentication code.
    *   ``state``: The encoded final URL to redirect to after successful authentication.
    """

    http_method_names = ["get"]
    """:meta private:"""

    next_page = LOGIN_REDIRECT_URL
    """:meta private:"""

    redirect_field_name = "state"
    """:meta private:"""

    def _error(self, request, message):
        error_message(request, message)
        return redirect("users:login")

    def get(self, request, *args, **kwargs):
        """:meta private:"""

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

        login(request, user)
        set_active_person(request, request.user.person)

        return HttpResponseRedirect(self.get_success_url())

    def get_redirect_url(self):
        """:meta private:"""

        return GoogleBackend.state_decode(super().get_redirect_url())


class UserAssignPermissionView(MultipleObjectMixin, UserAssignRemovePermissionView):
    """
    A view for assigning a permission to a user.

    **Success redirection view**: :class:`persons.views.PersonDetailView` of the person
    whose user account's permissions were changed.

    **Permissions**:

    Users with the ``povoleni`` permission.

    **Request body parameters**:

    *   ``permission``: The ID of the permission to be assigned.

    **Path parameters**:

    *   ``pk``: The ID of the person whose account's permissions should be changed.
    """

    success_message = _("Povolení úspěšně přidáno.")
    """:meta private:"""

    template_name = "users/assign_permission.html"
    """:meta private:"""

    context_object_name = "permissions"
    """:meta private:"""

    def get_context_data(self, **kwargs):
        """
        *   ``person``
        """
        self.object_list = self.get_queryset()

        kwargs.setdefault("person", self.object.person)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """:meta private:"""
        permissions = Permission.objects.all()
        user_permissions = self.object.user_permissions.values_list("pk", flat=True)

        for permission in permissions:
            permission.assigned = permission.pk in user_permissions

        return permissions

    @staticmethod
    def change_user_permission(user, permission):
        """
        Assigns the permission.
        """

        user.user_permissions.add(permission)


class UserRemovePermissionView(UserAssignRemovePermissionView):
    """
    A view for removing a permission from a user.

    **Success redirection view**: :class:`persons.views.PersonDetailView` of the person
    whose user account's permissions were changed.

    **Permissions**:

    Users with the ``povoleni`` permission.

    **Request body parameters**:

    *   ``permission``: The ID of the permission to be removed.

    **Path parameters**:

    *   ``pk``: The ID of the person whose account's permissions should be changed.
    """

    http_method_names = ["post"]
    """:meta private:"""

    success_message = _("Povolení úspěšně odebráno.")
    """:meta private:"""

    @staticmethod
    def change_user_permission(user, permission):
        """
        Removes the permission.
        """

        user.user_permissions.remove(permission)


class UserResetPasswordRequestView(SuccessMessageMixin, CreateView):
    """
    Requests a password reset for a user with the given email.

    Creates a password reset token and sends an email with a password reset link.

    **Success redirection view**: :class:`users.views.LoginView`

    **Request body parameters**:

    *   ``email``
    """

    form_class = UserResetPasswordRequestForm
    """:meta private:"""

    success_message = _("E-mail s odkazem pro změnu hesla byl odeslán.")
    """:meta private:"""

    success_url = reverse_lazy("users:login")
    """:meta private:"""

    template_name = "users/reset-password-request.html"
    """:meta private:"""

    def form_valid(self, form: UserResetPasswordRequestForm):
        """:meta private:"""

        response = super().form_valid(form)

        if form.user_found:
            token = self.object

            link = (
                f"{SERVER_PROTOCOL}://{SERVER_DOMAIN}"
                f"{reverse('users:reset-password')}?token={token.key}"
            )

            send_mail(
                subject=_("Zapomenuté heslo"),
                message=_("Nasledujte následující odkaz pro změnu hesla: {0}").format(
                    link
                ),
                recipient_list=[token.user.person.email],
            )

        return response


class UserResetPasswordView(SuccessMessageMixin, UpdateView):
    """
    Handles password reset requests. Deletes the token after the password is changed.

    This is the view that the user is redirected to after clicking the link
    in the password reset email.

    404 if the token has expired.

    **Success redirection view**: :class:`users.views.LoginView`

    **Query parameters**:

    *   ``token``: The password reset token.
    """

    form_class = UserChangePasswordRepeatForm
    """:meta private:"""

    success_message = _("Heslo změněno.")
    """:meta private:"""

    success_url = reverse_lazy("users:login")
    """:meta private:"""

    template_name = "users/reset-password.html"
    """:meta private:"""

    def get_object(self, queryset=None):
        """:meta private:"""

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
        """:meta private:"""

        response = super().form_valid(form)

        self.token.delete()

        return response


class LogoutView(BaseLogoutView):
    """
    Logs out the user.

    Sets a ``logout_remember`` cookie variable if the user doesn't want
    to confirm logouts anymore.

    **Request body parameters**:

    *   ``remember``: If set to ``true``,
        the user won't be asked to confirm logouts anymore.
    """

    def post(self, request, *args, **kwargs):
        """:meta private:"""

        form = LogoutForm(request.POST)

        response = super().post(request, *args, **kwargs)

        if form.is_valid() and form.cleaned_data["remember"]:
            response.set_cookie("logout_remember", "true")

        return response


class UserCreatePasswordView(
    UserCreateDeletePasswordPermissionMixin,
    SuccessMessageMixin,
    UserChangePasswordBaseMixin,
):
    """
    Creates a new user password.

    **Success redirection view**: :class:`persons.views.PersonDetailView`
    of the person whose user account password was created.

    **Permissions**:

    Users that can manage the person's membership type.

    **Request body parameters**:

    * ``person``: The ID of the person for whom a user account password should be created.
    """

    form_class = UserChangePasswordRepeatForm
    """:meta private:"""

    template_name = "users/create_password.html"
    """:meta private:"""

    def get_success_message(self, cleaned_data):
        """:meta private:"""

        return _(f"Heslo pro {self.object} bylo úspěšně přidáno.")


class UserDeletePasswordView(
    UserCreateDeletePasswordPermissionMixin, SuccessMessageMixin, UpdateView
):
    """
    Deletes a user's password.

    **Success redirection view**: :class:`persons.views.PersonDetailView`
    of the person whose password was deleted.

    **Permissions**:

    Users that can manage the person's membership type.

    **Path parameters**:

    *   ``pk``: The ID of the user whose password should be deleted.
    """

    context_object_name = "user_object"
    """:meta private:"""

    form_class = UserDeletePasswordForm
    """:meta private:"""

    model = User
    """:meta private:"""

    template_name = "users/delete_password.html"
    """:meta private:"""

    def get_success_url(self):
        """:meta private:"""

        return reverse("persons:detail", kwargs={"pk": self.person.pk})

    def form_valid(self, form):
        """:meta private:"""

        # success_message is sent after object deletion so we need to save the data
        # we will need later
        self.user_representation = str(self.object)
        self.person = self.object.person
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        """:meta private:"""

        return _(f"Heslo pro {self.user_representation} bylo úspěšně odstraněno.")
