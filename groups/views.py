from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages import error as error_message
from django.contrib.messages import success as success_message
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from google_integration import google_directory
from groups.utils import sync_single_group_with_google
from persons.views import PersonPermissionMixin
from vzs.mixin_extensions import MessagesMixin

from .forms import (
    AddMembersGroupForm,
    AddPersonToGroupForm,
    GroupForm,
    RemovePersonFromGroupForm,
)
from .models import Group, Person


class GroupPermissionMixin(PermissionRequiredMixin):
    permission_required = "groups.spravce_skupin"


class GroupIndexView(GroupPermissionMixin, ListView):
    context_object_name = "groups"
    model = Group
    template_name = "groups/index.html"


class GroupDeleteView(GroupPermissionMixin, SuccessMessageMixin, DeleteView):
    model = Group
    success_message = "Skupina byla úspěšně smazána."
    success_url = reverse_lazy("groups:index")
    template_name = "groups/delete.html"


class GroupDetailView(GroupPermissionMixin, DetailView):
    model = Group
    template_name = "groups/detail.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault(
            "available_persons",
            Person.objects.exclude(
                Q(groups__isnull=False) & Q(groups__id=self.object.pk)
            ),
        )

        return super().get_context_data(**kwargs)


class GroupAddMembersView(GroupPermissionMixin, SuccessMessageMixin, UpdateView):
    form_class = AddMembersGroupForm
    model = Group
    success_message = "Osoby byly úspěšně přidány."

    def get_success_url(self):
        return reverse("groups:detail", args=(self.object.pk,))

    def form_valid(self, form):
        new_members = form.cleaned_data["members"]

        existing_members = self.object.members.all()
        combined_members = existing_members | new_members

        form.instance.members.set(combined_members)
        del form.cleaned_data["members"]

        if form.instance.google_email:
            for new_member in new_members:
                if new_member.email is not None:
                    google_directory.add_member_to_group(
                        new_member.email, form.instance.google_email
                    )

        return super().form_valid(form)

    def form_invalid(self, form):
        error_message(self.request, _("Nepodařilo se přidat osoby."))
        return super().form_invalid(form)


class GroupCreateEditMixin(GroupPermissionMixin, SuccessMessageMixin):
    form_class = GroupForm
    model = Group
    success_message = "Skupina byla úspěšně uložena."
    template_name = "groups/edit.html"

    def get_success_url(self):
        return reverse(f"groups:detail", args=(self.object.pk,))

    def form_invalid(self, form):
        error_message(self.request, _("Skupinu se nepodařilo uložit."))
        return super().form_invalid(form)


class GroupCreateView(GroupCreateEditMixin, CreateView):
    pass


class GroupEditView(GroupCreateEditMixin, UpdateView):
    pass


class GroupRemoveMemberView(GroupPermissionMixin, SingleObjectMixin, View):
    model = Group
    pk_url_kwarg = "group_id"
    success_message = "Osoba byla odebrána."

    def get_success_url(self):
        return reverse(
            "groups:detail", args=(self.kwargs[GroupRemoveMemberView.pk_url_kwarg],)
        )

    def get(self, request, *args, person_id, **kwargs):
        group = self.get_object()

        member_to_remove_id = person_id

        group.members.remove(member_to_remove_id)

        if group.google_email:
            google_directory.remove_member_from_group(
                Person.objects.get(pk=member_to_remove_id).email, group.google_email
            )

        success_message(request, self.success_message)

        return redirect(self.get_success_url())


class SyncGroupMembersWithGoogleView(GroupPermissionMixin, SingleObjectMixin, View):
    http_method_names = ["get"]
    model = Group
    pk_url_kwarg = "group_id"

    def get(self, request, *args, **kwargs):
        group = self.get_object()

        if group.google_email is None:
            error_message(
                request,
                _(
                    "Zvolená skupina nemá zadanou google e-mailovou adresu, a proto nemůže být sychronizována."
                ),
            )

            return redirect(reverse("groups:detail", args=[group.pk]))

        sync_single_group_with_google(group)

        success_message(
            request,
            _("Synchronizace skupiny {} s Google Workplace byla úspěšná.").format(
                group.name
            ),
        )

        return redirect(reverse("groups:detail", args=[group.pk]))


class SyncGroupMembersWithGoogleAllView(GroupPermissionMixin, View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        for group in Group.objects.filter(google_email__isnull=False):
            sync_single_group_with_google(group)

        success_message(
            request,
            _("Synchronizace všech skupin s Google Workplace byla úspěšná."),
        )

        return redirect(reverse("groups:index"))


class AddRemovePersonToGroupMixin(PersonPermissionMixin, MessagesMixin, UpdateView):
    error_message: str
    http_method_names = ["post"]
    form_class: type

    def get_success_url(self) -> str:
        return reverse("persons:detail", args=[self.object])

    def get_error_message(self, errors):
        return self.error_message + " ".join(errors["group"])


class AddPersonToGroupView(AddRemovePersonToGroupMixin):
    form_class = AddPersonToGroupForm
    success_message = _("Osoba byla úspěšně přidána do skupiny.")
    error_message = _("Nepodařilo se přidat osobu do skupiny. ")


class RemovePersonFromGroupView(AddRemovePersonToGroupMixin):
    form_class = RemovePersonFromGroupForm
    success_message = _("Osoba byla úspěšně odebrána ze skupiny.")
    error_message = _("Nepodařilo se odebrat osobu ze skupiny. ")
