from django.views import generic
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import views as auth_views
from django.contrib.auth import models as auth_models
from django.utils.functional import SimpleLazyObject
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin

from persons.models import Person
from .models import User, Permission
from . import forms


class UserCreateView(SuccessMessageMixin, generic.edit.CreateView):
    template_name = "users/create.html"
    form_class = forms.UserCreateForm
    queryset = Person.objects.filter(user__isnull=True)

    def get_success_url(self):
        return reverse("persons:detail", kwargs={"pk": self.person.pk})

    def get_success_message(self, cleaned_data):
        return _(f"{self.object} byl úspěšně přidán.")

    def get_initial(self):
        return {"person": self.request.GET.get("person")}

    def dispatch(self, request, *args, **kwargs):
        self.person = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if "person" not in kwargs:
            kwargs["person"] = self.person

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "people" not in context:
            context["people"] = Person.objects.filter(user__isnull=True)

        if "user_create_form" not in context:
            context["user_create_form"] = context["form"]

        if "person_select_form" not in context:
            context["person_select_form"] = forms.PersonSelectForm(self.request.GET)

        if "person" not in context:
            context["person"] = self.person

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
    template_name = "users/change_password.html"
    form_class = forms.UserChangePasswordForm
    success_message = _("Heslo bylo úspěšně změněno.")

    def get_success_url(self):
        return reverse("persons:detail", kwargs={"pk": self.object.pk})


def set_active_person(request, person):
    request.session["_active_person_pk"] = person.pk


class LoginView(auth_views.LoginView):
    template_name = "users/login.html"
    authentication_form = forms.LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse("persons:detail", kwargs={"pk": self.request.user.person.pk})

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


class UserAssignRemovePermissionView(
    generic.detail.SingleObjectMixin, generic.edit.FormView
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


class UserAssignPermissionView(
    generic.list.MultipleObjectMixin, UserAssignRemovePermissionView
):
    template_name = "users/assign_permission.html"

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
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

    def _change_user_permission(self, user, permission):
        user.user_permissions.remove(permission)
