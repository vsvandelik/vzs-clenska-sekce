from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import BadRequest
from django.db import IntegrityError
from django.db.models import Exists, OuterRef
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from persons.models import Person
from persons.views import PersonPermissionMixin
from .forms import (
    FeatureForm,
    FeatureAssignmentByPersonForm,
    FeatureAssignmentByFeatureForm,
)
from .models import (
    FeatureAssignment,
    Feature,
    FeatureTypeTexts,
)
from .utils import extend_form_of_labels


class FeaturePermissionMixin(PermissionRequiredMixin):
    def __init__(self):
        super().__init__()
        self.feature_type = None
        self.feature_type_texts = None
        self.person = None

    def dispatch(self, request, feature_type, *args, **kwargs):
        self.feature_type = feature_type
        self.feature_type_texts = FeatureTypeTexts[feature_type]
        if "person" in kwargs:
            self.person = kwargs["person"]
        return super().dispatch(request, feature_type, *args, **kwargs)

    def has_permission(self):
        user = self.request.user
        return user.has_perm(self.feature_type_texts.permission_name)

    def get_context_data(self, **kwargs):
        kwargs.setdefault("texts", self.feature_type_texts)
        kwargs.setdefault("feature_type", self.feature_type)

        return super().get_context_data(**kwargs)

    def get_person_with_permission_check(self):
        try:
            return PersonPermissionMixin.get_queryset_by_permission(
                self.request.user
            ).get(id=self.person)
        except Person.DoesNotExist:
            raise Http404()


class FeatureAssignReturnEquipmentView(FeaturePermissionMixin, generic.View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        equipment_pk = kwargs["pk"]

        assigned_equipment = get_object_or_404(
            FeatureAssignment,
            pk=equipment_pk,
            feature__feature_type=Feature.Type.EQUIPMENT,
            person=self.person,
        )
        if assigned_equipment.date_returned:
            raise BadRequest("Vybavení již bylo vráceno.")

        assigned_equipment.date_returned = datetime.today()
        assigned_equipment.save()

        return redirect(reverse("persons:detail", args=[self.person]))


class FeatureAssignEditView(FeaturePermissionMixin, generic.edit.UpdateView):
    model = FeatureAssignment
    form_class = FeatureAssignmentByPersonForm
    template_name = "features_assignment/edit.html"

    def get_success_url(self):
        return reverse("persons:detail", args=[self.person])

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_context_data(self, **kwargs):
        kwargs.setdefault("person", self.get_person_with_permission_check())
        kwargs.setdefault(
            "features",
            Feature.objects.filter(
                feature_type=self.feature_type_texts.shortcut, assignable=True
            ),
        )

        return super().get_context_data(**kwargs)

    def get_form(self, form_class=None):
        return extend_form_of_labels(
            super().get_form(form_class), self.feature_type_texts.form_labels
        )

    def form_valid(self, form):
        form.instance.person = self.get_person_with_permission_check()

        if not form.instance.pk:
            success_message = self.feature_type_texts.success_message_assigned
        else:
            success_message = self.feature_type_texts.success_message_assigning_updated

        try:
            response = super().form_valid(form)
            form.add_transaction_if_necessary()
            messages.success(self.request, success_message)
            return response

        except IntegrityError:
            messages.error(
                self.request, self.feature_type_texts.duplicated_message_assigning
            )
            return super().form_invalid(form)

    def form_invalid(self, form):
        feature_name_4 = self.feature_type_texts.name_4
        messages.error(self.request, _(f"Nepodařilo se uložit {feature_name_4}."))

        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = self.feature_type_texts.shortcut
        kwargs["person"] = self.get_person_with_permission_check()
        return kwargs


class FeatureAssignDeleteView(
    FeaturePermissionMixin, SuccessMessageMixin, generic.edit.DeleteView
):
    model = FeatureAssignment
    template_name = "features_assignment/delete.html"

    def get_success_url(self):
        return reverse("persons:detail", args=[self.person])

    def get_success_message(self, cleaned_data):
        return self.feature_type_texts.success_message_assigning_delete

    def get_context_data(self, **kwargs):
        kwargs.setdefault("person", self.get_person_with_permission_check())

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        if (
            hasattr(self.object, "transaction")
            and not self.object.transaction.is_settled
        ):
            self.object.transaction.delete()

        return super().form_valid(form)


class FeatureIndexView(FeaturePermissionMixin, generic.ListView):
    model = Feature
    context_object_name = "features"

    def get_template_names(self):
        return f"features/index.html"

    def get_queryset(self):
        feature_type_params = self.feature_type_texts
        return super().get_queryset().filter(feature_type=feature_type_params.shortcut)


class FeatureDetailView(FeaturePermissionMixin, generic.DetailView):
    model = Feature

    def get_context_data(self, **kwargs):
        kwargs.setdefault("assignment_matrix", self._get_features_assignment_matrix())

        return super().get_context_data(**kwargs)

    def get_template_names(self):
        return f"features/detail.html"

    def get_queryset(self):
        feature_type_params = self.feature_type_texts
        return super().get_queryset().filter(feature_type=feature_type_params.shortcut)

    def _get_features_assignment_matrix(self):
        all_features = (
            self.object.get_descendants(include_self=True)
            .filter(assignable=True)
            .prefetch_related("featureassignment_set")
        )

        all_persons = Person.objects.filter(
            featureassignment__feature__in=all_features
        ).distinct()

        features_assignment_matrix = {
            "columns": all_features,
            "rows": [],
        }

        for person in all_persons:
            features = all_features.annotate(
                is_assigned=Exists(
                    FeatureAssignment.objects.filter(
                        person=person,
                        feature=OuterRef("pk"),
                        date_returned__isnull=True,
                    )
                )
            ).values_list("is_assigned", flat=True)

            assigned_features = list(features)

            if any(assigned_features):
                features_assignment_matrix["rows"].append(
                    {
                        "person": person,
                        "features": assigned_features,
                    }
                )

        return features_assignment_matrix


class FeatureEditView(FeaturePermissionMixin, generic.edit.UpdateView):
    model = Feature
    form_class = FeatureForm

    def get_template_names(self):
        return f"features/edit.html"

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_success_url(self):
        return reverse(f"{self.feature_type}:detail", args=(self.object.pk,))

    def form_valid(self, form):
        feature_type_texts = self.feature_type_texts
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
        feature_type_texts = self.feature_type_texts
        form = super().get_form(form_class)
        if feature_type_texts.form_labels:
            for field, label in feature_type_texts.form_labels.items():
                if field in form.fields:
                    form.fields[field].label = label

        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = self.feature_type_texts.shortcut
        return kwargs


class FeatureDeleteView(
    FeaturePermissionMixin, SuccessMessageMixin, generic.edit.DeleteView
):
    model = Feature

    def get_template_names(self):
        return f"features/delete.html"

    def get_success_url(self):
        return reverse(f"{self.feature_type}:index")

    def get_success_message(self, cleaned_data):
        return self.feature_type_texts.success_message_delete


class FeatureAssignToSelectedPersonView(
    FeaturePermissionMixin, SuccessMessageMixin, generic.edit.CreateView
):
    model = FeatureAssignment
    form_class = FeatureAssignmentByFeatureForm
    template_name = "features_assignment/assign_to_selected_person.html"
    success_message = _("Vlastnost byla úspěšně přiřazena.")

    def dispatch(self, request, feature_type, pk, *args, **kwargs):
        self.feature = get_object_or_404(Feature, pk=pk)
        return super().dispatch(request, feature_type, pk, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs.setdefault("feature", self.feature)

        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature"] = self.feature

        return kwargs

    def get_form(self, form_class=None):
        return extend_form_of_labels(
            super().get_form(form_class), self.feature_type_texts.form_labels
        )

    def get_success_url(self):
        return reverse(self.feature_type + ":detail", args=[self.feature.pk])

    def form_valid(self, form):
        response = super().form_valid(form)
        form.add_transaction_if_necessary()

        return response
