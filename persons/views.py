from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import (
    PersonForm,
    FeatureAssignmentForm,
    FeatureForm,
    StaticGroupForm,
    AddMembersStaticGroupForm,
)
from .models import (
    Person,
    FeatureAssignment,
    Feature,
    FeatureTypeTexts,
    Group,
    StaticGroup,
)


class IndexView(generic.ListView):
    model = Person
    template_name = "persons/index.html"
    context_object_name = "persons"


class DetailView(generic.DetailView):
    model = Person
    template_name = "persons/detail.html"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["qualifications"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"],
            feature__feature_type=Feature.Type.QUALIFICATION.value,
        )
        context["permissions"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"], feature__feature_type=Feature.Type.PERMIT.value
        )
        context["equipments"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"],
            feature__feature_type=Feature.Type.POSSESSION.value,
        )
        return context


class PersonCreateView(SuccessMessageMixin, generic.edit.CreateView):
    model = Person
    template_name = "persons/edit.html"
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
    template_name = "persons/edit.html"
    form_class = PersonForm
    success_message = _("Osoba byla úspěšně upravena")

    def form_invalid(self, form):
        messages.error(
            self.request, _("Změny se nepodařilo uložit. Opravte chyby ve formuláři.")
        )
        return super().form_invalid(form)


class PersonDeleteView(generic.edit.DeleteView):
    model = Person
    template_name = "persons/confirm_delete.html"
    success_url = reverse_lazy("persons:index")
    success_message = _("Osoba byla úspěšně smazána")


class FeatureAssignEditView(generic.edit.UpdateView):
    model = FeatureAssignment
    form_class = FeatureAssignmentForm
    template_name = "persons/features_assignment_edit.html"

    def get_success_url(self):
        return reverse("persons:detail", args=[self.kwargs["person"]])

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["type"] = FeatureTypeTexts[self.kwargs["feature_type"]].name_4
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
    template_name = "persons/features_assignment_delete.html"

    def get_success_url(self):
        return reverse("persons:detail", args=[self.kwargs["person"]])

    def get_success_message(self, cleaned_data):
        return FeatureTypeTexts[
            self.kwargs["feature_type"]
        ].success_message_assigning_delete

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["type"] = FeatureTypeTexts[self.kwargs["feature_type"]].name_4
        context["person"] = get_object_or_404(Person, id=self.kwargs["person"])
        return context


class FeatureIndex(generic.ListView):
    model = Feature
    context_object_name = "features"

    def get_template_names(self):
        return f"persons/{self.kwargs['feature_type']}_index.html"

    def get_queryset(self):
        feature_type_params = FeatureTypeTexts[self.kwargs["feature_type"]]
        return (
            super()
            .get_queryset()
            .filter(feature_type=feature_type_params.shortcut, parent=None)
        )


class FeatureDetail(generic.DetailView):
    model = Feature

    def get_template_names(self):
        return f"persons/{self.kwargs['feature_type']}_detail.html"

    def get_queryset(self):
        feature_type_params = FeatureTypeTexts[self.kwargs["feature_type"]]
        return super().get_queryset().filter(feature_type=feature_type_params.shortcut)


class FeatureEdit(generic.edit.UpdateView):
    model = Feature
    form_class = FeatureForm

    def get_template_names(self):
        return f"persons/{self.kwargs['feature_type']}_edit.html"

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


class FeatureDelete(SuccessMessageMixin, generic.edit.DeleteView):
    model = Feature

    def get_template_names(self):
        return f"persons/{self.kwargs['feature_type']}_delete.html"

    def get_success_url(self):
        return reverse(f"{self.kwargs['feature_type']}:index")

    def get_success_message(self, cleaned_data):
        return FeatureTypeTexts[self.kwargs["feature_type"]].success_message_delete


class GroupIndex(generic.ListView):
    model = Group
    template_name = "persons/groups_index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["static_groups"] = StaticGroup.objects.all()
        context["dynamic_groups"] = StaticGroup.objects.all()
        return context


class GroupDeleteView(SuccessMessageMixin, generic.edit.DeleteView):
    model = StaticGroup
    template_name = "persons/groups_delete.html"
    success_url = reverse_lazy("persons:groups:index")
    success_message = "Skupina byla úspěšně smazána."


class StaticGroupDetail(
    SuccessMessageMixin, generic.DetailView, generic.edit.UpdateView
):
    model = StaticGroup
    form_class = AddMembersStaticGroupForm
    success_message = "Osoby byly úspěšně přidány."
    template_name = "persons/groups_detail_static.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["available_persons"] = Person.objects.exclude(
            Q(staticgroup__isnull=False) & Q(staticgroup__id=self.object.pk)
        )
        return context

    def get_success_url(self):
        return reverse("persons:groups:detail", args=(self.object.pk,))

    def form_valid(self, form):
        new_member_ids = form.cleaned_data["members"]

        existing_members = self.object.members.all()
        combined_members = existing_members | new_member_ids

        form.instance.members.set(combined_members)

        messages.success(self.request, self.success_message)

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, _("Nepodařilo se přidat osoby."))
        return super().form_invalid(form)


class StaticGroupEditView(SuccessMessageMixin, generic.edit.UpdateView):
    model = StaticGroup
    form_class = StaticGroupForm
    template_name = "persons/groups_edit_static.html"
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

        messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())
