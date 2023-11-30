from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from google_integration import google_directory
from groups.utils import sync_single_group_with_google
from persons.views import PersonPermissionMixin
from .forms import (
    GroupForm,
    AddMembersGroupForm,
    AddPersonToGroupForm,
    RemovePersonFromGroupForm,
)
from .models import Person, Group


class GroupPermissionMixin(PermissionRequiredMixin):
    permission_required = "groups.spravce_skupin"


class GroupIndexView(GroupPermissionMixin, generic.ListView):
    model = Group
    context_object_name = "groups"
    template_name = "groups/index.html"


class GroupDeleteView(
    GroupPermissionMixin, SuccessMessageMixin, generic.edit.DeleteView
):
    model = Group
    template_name = "groups/delete.html"
    success_url = reverse_lazy("groups:index")
    success_message = "Skupina byla úspěšně smazána."


class GroupDetailView(
    GroupPermissionMixin,
    SuccessMessageMixin,
    generic.DetailView,
    generic.edit.UpdateView,
):
    model = Group
    form_class = AddMembersGroupForm
    success_message = "Osoby byly úspěšně přidány."
    template_name = "groups/detail.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault(
            "available_persons",
            Person.objects.exclude(
                Q(groups__isnull=False) & Q(groups__id=self.object.pk)
            ),
        )

        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse("groups:detail", args=(self.object.pk,))

    def form_valid(self, form):
        new_members = form.cleaned_data["members"]

        existing_members = self.object.members.all()
        combined_members = existing_members | new_members

        form.instance.members.set(combined_members)

        if form.instance.google_email:
            for new_member in new_members:
                if new_member.email is not None:
                    google_directory.add_member_to_group(
                        new_member.email, form.instance.google_email
                    )

        messages.success(self.request, self.success_message)

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, _("Nepodařilo se přidat osoby."))
        return super().form_invalid(form)


class GroupEditView(GroupPermissionMixin, SuccessMessageMixin, generic.edit.UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "groups/edit.html"
    success_message = "Skupina byla úspěšně uložena."

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_success_url(self):
        return reverse(f"groups:detail", args=(self.object.pk,))

    def form_invalid(self, form):
        messages.error(self.request, _("Skupinu se nepodařilo uložit."))
        return super().form_invalid(form)


class GroupRemoveMemberView(GroupPermissionMixin, generic.View):
    success_message = "Osoba byla odebrána."

    def get_success_url(self):
        return reverse("groups:detail", args=(self.kwargs["group"],))

    def get(self, request, *args, **kwargs):
        member_to_remove = self.kwargs["person"]

        group = get_object_or_404(Group, id=self.kwargs["group"])
        group.members.remove(member_to_remove)

        if group.google_email:
            google_directory.remove_member_from_group(
                Person.objects.get(pk=member_to_remove).email, group.google_email
            )

        messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())


class SyncGroupMembersWithGoogleView(GroupPermissionMixin, generic.View):
    http_method_names = ["get"]

    def get(self, request, group=None):
        if group:
            group_instance = get_object_or_404(Group, pk=group)
            if not group_instance.google_email:
                messages.error(
                    request,
                    _(
                        "Zvolená skupina nemá zadanou google e-mailovou adresu, a proto nemůže být sychronizována."
                    ),
                )
                return redirect(reverse("groups:detail", args=[group_instance.pk]))

            sync_single_group_with_google(group_instance)
            messages.success(
                request,
                _("Synchronizace skupiny %s s Google Workplace byla úspěšná.")
                % group_instance.name,
            )
            return redirect(reverse("groups:detail", args=[group_instance.pk]))

        else:
            for group in Group.objects.filter(google_email__isnull=False):
                sync_single_group_with_google(group)

            messages.success(
                request,
                _("Synchronizace všech skupin s Google Workplace byla úspěšná."),
            )
            return redirect(reverse("groups:index"))


class AddRemovePersonToGroupMixin(PersonPermissionMixin, generic.View):
    http_method_names = ["post"]

    ADD_TO_GROUP = "add"
    REMOVE_FROM_GROUP = "remove"

    def process_form(
        self, request, form, person_pk, op, success_message, error_message
    ):
        if form.is_valid():
            group = form.cleaned_data["group"]

            if op == self.ADD_TO_GROUP:
                group.members.add(person_pk)
            else:
                group.members.remove(person_pk)

            messages.success(request, success_message)

        else:
            person_error_messages = " ".join(form.errors["group"])
            messages.error(request, error_message + person_error_messages)

        return redirect(reverse("persons:detail", args=[person_pk]))


class AddPersonToGroupView(AddRemovePersonToGroupMixin):
    def post(self, request, pk):
        form = AddPersonToGroupForm(request.POST, person=Person.objects.get(pk=pk))

        return self.process_form(
            request,
            form,
            pk,
            AddRemovePersonToGroupMixin.ADD_TO_GROUP,
            _("Osoba byla úspěšně přidána do skupiny."),
            _("Nepodařilo se přidat osobu do skupiny. "),
        )


class RemovePersonFromGroupView(AddRemovePersonToGroupMixin):
    def post(self, request, pk):
        form = RemovePersonFromGroupForm(request.POST, person=Person.objects.get(pk=pk))

        return self.process_form(
            request,
            form,
            pk,
            AddRemovePersonToGroupMixin.REMOVE_FROM_GROUP,
            _("Osoba byla úspěšně odebrána ze skupiny."),
            _("Nepodařilo se odebrat osobu ze skupiny. "),
        )
