import csv

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from google_integration import google_directory
from .forms import (
    PersonForm,
    FeatureAssignmentForm,
    FeatureForm,
    StaticGroupForm,
    AddMembersStaticGroupForm,
    AddManagedPersonForm,
    DeleteManagedPersonForm,
)
from .models import (
    Person,
    FeatureAssignment,
    Feature,
    FeatureTypeTexts,
    Group,
    StaticGroup,
)
from .utils import sync_single_group_with_google


class PersonIndexView(generic.ListView):
    model = Person
    template_name = "persons/persons/index.html"
    context_object_name = "persons"
    paginate_by = 20


class PersonDetailView(generic.DetailView):
    model = Person
    template_name = "persons/persons/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["qualifications"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"],
            feature__feature_type=Feature.Type.QUALIFICATION.value,
        )
        context["permissions"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"],
            feature__feature_type=Feature.Type.PERMISSION.value,
        )
        context["equipments"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"],
            feature__feature_type=Feature.Type.EQUIPMENT.value,
        )
        context["persons_to_manage"] = Person.objects.exclude(
            managed_by=self.kwargs["pk"]
        ).exclude(pk=self.kwargs["pk"])
        return context


class PersonCreateView(SuccessMessageMixin, generic.edit.CreateView):
    model = Person
    template_name = "persons/persons/edit.html"
    form_class = PersonForm
    success_message = _("Osoba byla úspěšně vytvořena")

    def form_invalid(self, form):
        messages.error(
            self.request,
            _("Nepodařilo se vytvořit novou osobu. Opravte chyby ve formuláři."),
        )
        return super().form_invalid(form)


class PersonUpdateView(SuccessMessageMixin, generic.edit.UpdateView):
    model = Person
    template_name = "persons/persons/edit.html"
    form_class = PersonForm
    success_message = _("Osoba byla úspěšně upravena")

    def form_invalid(self, form):
        messages.error(
            self.request, _("Změny se nepodařilo uložit. Opravte chyby ve formuláři.")
        )
        return super().form_invalid(form)


class PersonDeleteView(generic.edit.DeleteView):
    model = Person
    template_name = "persons/persons/confirm_delete.html"
    success_url = reverse_lazy("persons:index")
    success_message = _("Osoba byla úspěšně smazána")


class FeatureAssignEditView(generic.edit.UpdateView):
    model = FeatureAssignment
    form_class = FeatureAssignmentForm
    template_name = "persons/features_assignment/edit.html"

    def get_success_url(self):
        return reverse("persons:detail", args=[self.kwargs["person"]])

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feature_type_texts = FeatureTypeTexts[self.kwargs["feature_type"]]
        context["texts"] = feature_type_texts
        context["features"] = Feature.objects.filter(
            feature_type=feature_type_texts.shortcut, assignable=True
        )
        context["person"] = get_object_or_404(Person, id=self.kwargs["person"])
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form_labels = FeatureTypeTexts[self.kwargs["feature_type"]].form_labels
        if form_labels:
            for field, label in form_labels.items():
                if field in form.fields:
                    form.fields[field].label = label

        return form

    def form_valid(self, form):
        form.instance.person = get_object_or_404(Person, id=self.kwargs["person"])
        feature_type_texts = FeatureTypeTexts[self.kwargs["feature_type"]]

        if not form.instance.pk:
            success_message = feature_type_texts.success_message_assigned
        else:
            success_message = feature_type_texts.success_message_assigning_updated

        try:
            response = super().form_valid(form)
            messages.success(self.request, success_message)
            return response

        except IntegrityError:
            messages.error(
                self.request, feature_type_texts.duplicated_message_assigning
            )
            return super().form_invalid(form)

    def form_invalid(self, form):
        feature_name_4 = FeatureTypeTexts[self.kwargs["feature_type"]].name_4
        messages.error(self.request, _(f"Nepodařilo se uložit {feature_name_4}."))

        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = FeatureTypeTexts[self.kwargs["feature_type"]].shortcut
        return kwargs


class FeatureAssignDeleteView(SuccessMessageMixin, generic.edit.DeleteView):
    model = FeatureAssignment
    template_name = "persons/features_assignment/delete.html"

    def get_success_url(self):
        return reverse("persons:detail", args=[self.kwargs["person"]])

    def get_success_message(self, cleaned_data):
        return FeatureTypeTexts[
            self.kwargs["feature_type"]
        ].success_message_assigning_delete

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["texts"] = FeatureTypeTexts[self.kwargs["feature_type"]]
        context["person"] = get_object_or_404(Person, id=self.kwargs["person"])
        return context


class FeatureIndexView(generic.ListView):
    model = Feature
    context_object_name = "features"

    def get_template_names(self):
        return f"persons/features/index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["texts"] = FeatureTypeTexts[self.kwargs["feature_type"]]
        context["feature_type"] = self.kwargs["feature_type"]
        return context

    def get_queryset(self):
        feature_type_params = FeatureTypeTexts[self.kwargs["feature_type"]]
        return (
            super()
            .get_queryset()
            .filter(feature_type=feature_type_params.shortcut, parent=None)
        )


class FeatureDetailView(generic.DetailView):
    model = Feature

    def get_template_names(self):
        return f"persons/features/detail.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["texts"] = FeatureTypeTexts[self.kwargs["feature_type"]]
        context["feature_type"] = self.kwargs["feature_type"]
        return context

    def get_queryset(self):
        feature_type_params = FeatureTypeTexts[self.kwargs["feature_type"]]
        return super().get_queryset().filter(feature_type=feature_type_params.shortcut)


class FeatureEditView(generic.edit.UpdateView):
    model = Feature
    form_class = FeatureForm

    def get_template_names(self):
        return f"persons/features/edit.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["texts"] = FeatureTypeTexts[self.kwargs["feature_type"]]
        return context

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_success_url(self):
        return reverse(f"{self.kwargs['feature_type']}:detail", args=(self.object.pk,))

    def form_valid(self, form):
        feature_type_texts = FeatureTypeTexts[self.kwargs["feature_type"]]
        form.instance.feature_type = feature_type_texts.shortcut
        messages.success(self.request, feature_type_texts.success_message_save)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            _("Formulář se nepodařilo uložit. Opravte chyby a zkuste to znovu."),
        )
        return super().form_invalid(form)

    def get_form(self, form_class=None):
        feature_type_texts = FeatureTypeTexts[self.kwargs["feature_type"]]
        form = super().get_form(form_class)
        if feature_type_texts.form_labels:
            for field, label in feature_type_texts.form_labels.items():
                if field in form.fields:
                    form.fields[field].label = label

        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = FeatureTypeTexts[self.kwargs["feature_type"]].shortcut
        return kwargs


class FeatureDeleteView(SuccessMessageMixin, generic.edit.DeleteView):
    model = Feature

    def get_template_names(self):
        return f"persons/features/delete.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["texts"] = FeatureTypeTexts[self.kwargs["feature_type"]]
        return context

    def get_success_url(self):
        return reverse(f"{self.kwargs['feature_type']}:index")

    def get_success_message(self, cleaned_data):
        return FeatureTypeTexts[self.kwargs["feature_type"]].success_message_delete


class GroupIndexView(generic.ListView):
    model = Group
    template_name = "persons/groups/index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["static_groups"] = StaticGroup.objects.all()
        context["dynamic_groups"] = StaticGroup.objects.all()
        return context


class GroupDeleteView(SuccessMessageMixin, generic.edit.DeleteView):
    model = StaticGroup
    template_name = "persons/groups/delete.html"
    success_url = reverse_lazy("persons:groups:index")
    success_message = "Skupina byla úspěšně smazána."


class StaticGroupDetailView(
    SuccessMessageMixin, generic.DetailView, generic.edit.UpdateView
):
    model = StaticGroup
    form_class = AddMembersStaticGroupForm
    success_message = "Osoby byly úspěšně přidány."
    template_name = "persons/groups/detail_static.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["available_persons"] = Person.objects.exclude(
            Q(groups__isnull=False) & Q(groups__id=self.object.pk)
        )
        return context

    def get_success_url(self):
        return reverse("persons:groups:detail", args=(self.object.pk,))

    def form_valid(self, form):
        new_members = form.cleaned_data["members"]

        existing_members = self.object.members.all()
        combined_members = existing_members | new_members

        form.instance.members.set(combined_members)

        if form.instance.google_email:
            for new_member in new_members:
                google_directory.add_member_to_group(
                    new_member.email, form.instance.google_email
                )

        messages.success(self.request, self.success_message)

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, _("Nepodařilo se přidat osoby."))
        return super().form_invalid(form)


class StaticGroupEditView(SuccessMessageMixin, generic.edit.UpdateView):
    model = StaticGroup
    form_class = StaticGroupForm
    template_name = "persons/groups/edit_static.html"
    success_message = "Statická skupina byla úspěšně uložena."

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_success_url(self):
        return reverse(f"persons:groups:detail", args=(self.object.pk,))

    def form_invalid(self, form):
        messages.error(self.request, _("Skupinu se nepodařilo uložit."))
        return super().form_invalid(form)


class StaticGroupRemoveMemberView(generic.View):
    success_message = "Osoba byla odebrána."

    def get_success_url(self):
        return reverse("persons:groups:detail", args=(self.kwargs["group"],))

    def get(self, request, *args, **kwargs):
        member_to_remove = self.kwargs["person"]

        static_group = get_object_or_404(StaticGroup, id=self.kwargs["group"])
        static_group.members.remove(member_to_remove)

        if static_group.google_email:
            google_directory.remove_member_from_group(
                Person.objects.get(pk=member_to_remove).email, static_group.google_email
            )

        messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())


class SyncGroupMembersWithGoogleView(generic.View):
    http_method_names = ["get"]

    def get(self, request, group=None):
        if group:
            group_instance = get_object_or_404(StaticGroup, pk=group)
            if not group_instance.google_email:
                messages.error(
                    request,
                    _(
                        "Zvolená skupina nemá zadanou google e-mailovou adresu, a proto nemůže být sychronizována."
                    ),
                )
                return redirect(
                    reverse("persons:groups:detail", args=[group_instance.pk])
                )

            sync_single_group_with_google(group_instance)
            messages.success(
                request,
                _("Synchronizace skupiny %s s Google Workplace byla úspěšná.")
                % group_instance.name,
            )
            return redirect(reverse("persons:groups:detail", args=[group_instance.pk]))

        else:
            for group in StaticGroup.objects.filter(google_email__isnull=False):
                sync_single_group_with_google(group)

            messages.success(
                request,
                _("Synchronizace všech skupin s Google Workplace byla úspěšná."),
            )
            return redirect(reverse("persons:groups:index"))


class AddDeleteManagedPersonMixin(generic.View):
    http_method_names = ["post"]

    def process_form(self, request, form, pk, op, success_message, error_message):
        if form.is_valid():
            managing_person = form.cleaned_data["managing_person_instance"]
            new_managed_person = form.cleaned_data["managed_person_instance"]

            if op == "add":
                managing_person.managed_persons.add(new_managed_person)
            else:
                managing_person.managed_persons.remove(new_managed_person)

            messages.success(request, success_message)

        else:
            person_error_messages = " ".join(form.errors["person"])
            messages.error(request, error_message + person_error_messages)

        return redirect(reverse("persons:detail", args=[pk]))


class AddManagedPersonView(AddDeleteManagedPersonMixin):
    def post(self, request, pk):
        form = AddManagedPersonForm(request.POST, managing_person=pk)

        return self.process_form(
            request,
            form,
            pk,
            "add",
            _("Nová spravovaná osoba byla přidána."),
            _("Nepodařilo se uložit novou spravovanou osobu. "),
        )


class DeleteManagedPersonView(AddDeleteManagedPersonMixin):
    def post(self, request, pk):
        form = DeleteManagedPersonForm(request.POST, managing_person=pk)

        return self.process_form(
            request,
            form,
            pk,
            "delete",
            _("Odebrání spravované osoby bylo úspěšné."),
            _("Nepodařilo se odebrat spravovanou osobu. "),
        )


class SendEmailToSelectedPersonsView(generic.View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        # selected_persons_id = request.GET.getlist('persons', [])
        # selected_persons = Person.objects.filter(pk__in=selected_persons_id)

        # TODO: Adjust this filtering person based on displayed persons in table
        selected_persons = Person.objects.all()

        recipients = [
            f"{p.first_name} {p.last_name} <{p.email}>" for p in selected_persons
        ]

        gmail_link = "https://mail.google.com/mail/?view=cm&to=" + ",".join(recipients)

        return redirect(gmail_link)


class ExportSelectedPersonsView(generic.View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        # selected_persons_id = request.GET.getlist('persons', [])
        # selected_persons = Person.objects.filter(pk__in=selected_persons_id)

        # TODO: Adjust this filtering person based on displayed persons in table
        selected_persons = Person.objects.all()

        response = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="vzs_osoby_export.csv"'
            },
        )
        response.write("\ufeff".encode("utf8"))

        writer = csv.writer(response, delimiter=";")

        labels = []
        keys = []

        for field in Person._meta.get_fields():
            if field.is_relation:
                continue

            labels.append(
                field.verbose_name if hasattr(field, "verbose_name") else field.name
            )
            keys.append(field.name)

        writer.writerow(labels)  # header

        for person in selected_persons:
            writer.writerow([getattr(person, key) for key in keys])

        return response
