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
from vzs.mixins import MessagesMixin
from .forms import (
    AddMembersGroupForm,
    AddPersonToGroupForm,
    GroupForm,
    RemovePersonFromGroupForm,
)
from .models import Group, Person
from .permissions import GroupPermissionMixin


class GroupIndexView(GroupPermissionMixin, ListView):
    """
    Displays the list of all groups.

    **Permissions**:

    Users with ``skupiny`` permission.
    """

    context_object_name = "groups"
    model = Group
    template_name = "groups/index.html"


class GroupDeleteView(GroupPermissionMixin, SuccessMessageMixin, DeleteView):
    """
    Deletes a group.

    **Success redirection view**: :class:`groups.views.GroupIndexView`

    **Permissions**:

    Users with ``skupiny`` permission.

    **Path parameters**:

    *   ``pk`` - group ID
    """

    model = Group
    success_message = "Skupina byla úspěšně smazána."
    success_url = reverse_lazy("groups:index")
    template_name = "groups/delete.html"


class GroupDetailView(GroupPermissionMixin, DetailView):
    """
    Displays the detail of a group.

    Allows selecting persons to be added to the group.

    **Permissions**:

    Users with ``skupiny`` permission.

    **Path parameters**:

    *   ``pk`` - group ID
    """

    model = Group
    template_name = "groups/detail.html"

    def get_context_data(self, **kwargs):
        """
        *   ``available_persons`` - persons who can be added to the group
        """

        kwargs.setdefault(
            "available_persons",
            Person.objects.exclude(
                Q(groups__isnull=False) & Q(groups__id=self.object.pk)
            ),
        )

        return super().get_context_data(**kwargs)


class GroupAddMembersView(GroupPermissionMixin, MessagesMixin, UpdateView):
    """
    Adds persons to a group.

    Also adds the persons to the Google group if the group has one specified.

    **Success redirection view**: :class:`groups.views.GroupDetailView`

    **Permissions**:

    Users with ``skupiny`` permission.

    **Path parameters**:

    *   ``pk`` - group ID

    **Request body parameters**:

    *   ``members`` - list of persons to be added to the group
    """

    error_message = _("Nepodařilo se přidat osoby.")
    form_class = AddMembersGroupForm
    model = Group
    success_message = _("Osoby byly úspěšně přidány.")

    def get_success_url(self):
        """:meta private:"""

        return reverse("groups:detail", args=(self.object.pk,))

    def form_valid(self, form):
        """:meta private:"""

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


class GroupCreateEditMixin(GroupPermissionMixin, MessagesMixin):
    """:meta private:"""

    error_message = _("Skupinu se nepodařilo uložit.")
    form_class = GroupForm
    model = Group
    success_message = _("Skupina byla úspěšně uložena.")
    template_name = "groups/edit.html"

    def get_success_url(self):
        return reverse(f"groups:detail", args=(self.object.pk,))


class GroupCreateView(GroupCreateEditMixin, CreateView):
    """
    Creates a new group.

    **Success redirection view**: :class:`groups.views.GroupDetailView`

    **Permissions**:

    Users with ``skupiny`` permission.

    **Request body parameters**:

    *   ``name``
    *   ``google_email``
    *   ``google_as_members_authority``
    """

    pass


class GroupEditView(GroupCreateEditMixin, UpdateView):
    """
    Edits a group.

    **Success redirection view**: :class:`groups.views.GroupDetailView`

    **Permissions**:

    Users with ``skupiny`` permission.

    **Request body parameters**:

    *   ``name``
    *   ``google_email``
    *   ``google_as_members_authority``
    """

    pass


class GroupRemoveMemberView(GroupPermissionMixin, SingleObjectMixin, View):
    """
    Removes a person from the group.

    Also removes the person from the Google group if the group has one specified.

    **Success redirection view**: :class:`groups.views.GroupDetailView`

    **Permissions**:

    Users with ``skupiny`` permission.

    **Path parameters**:

    *   ``group_id`` - group ID
    *   ``person_id`` - person ID
    """

    model = Group
    pk_url_kwarg = "group_id"
    success_message = _("Osoba byla odebrána.")

    def get_success_url(self):
        """:meta private:"""

        return reverse(
            "groups:detail", args=(self.kwargs[GroupRemoveMemberView.pk_url_kwarg],)
        )

    def get(self, request, *args, person_id, **kwargs):
        """:meta private:"""

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
    """
    Synchronizes the group with its Google group, if it has one specified.

    See :func:`groups.utils.sync_single_group_with_google` for more info.

    **Permissions**:

    Users with ``skupiny`` permission.

    **Path parameters**:

    *   ``group_id`` - group ID
    """

    http_method_names = ["get"]
    model = Group
    pk_url_kwarg = "group_id"
    success_message = _(
        "Synchronizace skupiny {group_name} s Google Workplace byla úspěšná."
    )

    def get(self, request, *args, **kwargs):
        """:meta private:"""

        group = self.get_object()

        if group.google_email is None:
            error_message(
                request,
                _(
                    "Zvolená skupina nemá zadanou google e-mailovou adresu,"
                    "a proto nemůže být sychronizována."
                ),
            )

            return redirect(reverse("groups:detail", args=[group.pk]))

        sync_single_group_with_google(group)

        success_message(
            request,
            self.success_message.format(group_name=group.name),
        )

        return redirect(reverse("groups:detail", args=[group.pk]))


class SyncGroupMembersWithGoogleAllView(GroupPermissionMixin, View):
    """
    Synchronizes all groups with their Google groups.

    See :class:`SyncGroupMembersWithGoogleView`
    and  :func:`groups.utils.sync_single_group_with_google` for more info.

    **Permissions**:

    Users with ``skupiny`` permission.
    """

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        """:meta private:"""

        for group in Group.objects.filter(google_email__isnull=False):
            sync_single_group_with_google(group)

        success_message(
            request,
            _("Synchronizace všech skupin s Google Workplace byla úspěšná."),
        )

        return redirect(reverse("groups:index"))


class AddRemovePersonToGroupMixin(PersonPermissionMixin, MessagesMixin, UpdateView):
    """:meta private:"""

    error_message: str
    form_class: type
    http_method_names = ["post"]
    model = Person

    def get_success_url(self) -> str:
        return reverse("persons:detail", args=[self.object.pk])

    def get_error_message(self, errors):
        return self.error_message + " ".join(errors["group"])


class AddPersonToGroupView(AddRemovePersonToGroupMixin):
    """
    Adds a person to a group.

    **Success redirection view**: :class:`persons.views.PersonDetailView`

    **Permissions**:

    Users that manage the person's membership type.

    **Path parameters**:

    *   ``pk`` - person ID

    **Request body parameters**:

    *   ``group`` - group ID
    """

    error_message = _("Nepodařilo se přidat osobu do skupiny. ")
    form_class = AddPersonToGroupForm
    success_message = _("Osoba byla úspěšně přidána do skupiny.")


class RemovePersonFromGroupView(AddRemovePersonToGroupMixin):
    """
    Removes a person from a group.

    **Success redirection view**: :class:`persons.views.PersonDetailView`

    **Permissions**:

    Users that manage the person's membership type.

    **Path parameters**:

    *   ``pk`` - person ID

    **Request body parameters**:

    *   ``group`` - group ID
    """

    error_message = _("Nepodařilo se odebrat osobu ze skupiny. ")
    form_class = RemovePersonFromGroupForm
    success_message = _("Osoba byla úspěšně odebrána ze skupiny.")
