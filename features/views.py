from django.contrib.messages import error as error_message
from django.contrib.messages import success as success_message
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import BadRequest
from django.db import IntegrityError
from django.db.models import Exists, OuterRef, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from persons.models import Person
from persons.views import PersonPermissionMixin
from vzs.mixin_extensions import MessagesMixin
from vzs.utils import today

from .forms import (
    FeatureAssignmentByFeatureForm,
    FeatureAssignmentByPersonForm,
    FeatureForm,
)
from .models import Feature, FeatureAssignment, FeatureTypeTexts
from .permissions import FeaturePermissionMixin
from .utils import extend_form_of_labels


class FeatureMixin(FeaturePermissionMixin):
    """:meta private:"""

    def __init__(self):
        """:meta private:"""

        super().__init__()

        self.feature_type = None
        self.feature_type_texts = None
        self.person = None

    def dispatch(self, request, feature_type, *args, **kwargs):
        """:meta private:"""

        self.feature_type = feature_type
        self.feature_type_texts = FeatureTypeTexts[feature_type]

        if "person" in kwargs:
            self.person = kwargs["person"]

        return super().dispatch(request, feature_type, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """:meta private:"""

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


class FeatureAssignReturnEquipmentView(FeatureMixin, View):
    """
    Returns a piece of equipment borrowed by a person.
    Sets the date of return to today.

    **Success redirection view**: :class:`persons.views.PersonDetailView`

    **Permissions**:

    Users with permission ``vybaveni``.

    **Path parameters**:

    *   ``person`` - person ID
    *   ``pk`` - equipment ID
    """

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        """:meta private:"""

        equipment_pk = kwargs["pk"]

        assigned_equipment = get_object_or_404(
            FeatureAssignment,
            pk=equipment_pk,
            feature__feature_type=Feature.Type.EQUIPMENT,
            person=self.person,
        )

        if assigned_equipment.date_returned:
            raise BadRequest("Vybavení již bylo vráceno.")

        assigned_equipment.date_returned = today()
        assigned_equipment.save()

        return redirect("persons:detail", self.person)


class FeatureAssignEditView(FeatureMixin, UpdateView):
    """
    Assigns a feature of a certain category to a person or edits an existing assignment.

    **Success redirection view**: :class:`persons.views.PersonDetailView`

    **Permissions**:

    Users with the appropriate feature category permission.

    **View parameters**:

    *   ``feature_type`` - feature category

    **Path parameters**:

    *   ``person`` - person ID
    *   ``pk``? - feature assignment ID, necessary for editing

    **Request body parameters**:

    *   ``feature``
    *   ``date_assigned``
    *   ``date_expire``
    *   ``date_returned``
    *   ``issuer``
    *   ``code``
    """

    form_class = FeatureAssignmentByPersonForm
    model = FeatureAssignment
    template_name = "features_assignment/edit.html"

    def get_success_url(self):
        """:meta private:"""

        return reverse("persons:detail", args=[self.person])

    def get_object(self, queryset=None):
        """:meta private:"""

        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_context_data(self, **kwargs):
        """
        *   ``person``
        *   ``features`` - assignable features of the category
        """

        kwargs.setdefault("person", self.get_person_with_permission_check())
        kwargs.setdefault(
            "features",
            Feature.objects.filter(
                feature_type=self.feature_type_texts.shortcut, assignable=True
            ),
        )

        return super().get_context_data(**kwargs)

    def get_form(self, form_class=None):
        """:meta private:"""

        form = super().get_form(form_class)

        return extend_form_of_labels(form, self.feature_type_texts.form_labels)

    def form_valid(self, form):
        """:meta private:"""

        form.instance.person = self.get_person_with_permission_check()

        if not form.instance.pk:
            success_message_text = self.feature_type_texts.success_message_assigned
        else:
            success_message_text = (
                self.feature_type_texts.success_message_assigning_updated
            )

        try:
            response = super().form_valid(form)
            form.add_transaction_if_necessary()
            success_message(self.request, success_message_text)
            return response

        except IntegrityError:
            error_message(
                self.request, self.feature_type_texts.duplicated_message_assigning
            )
            return super().form_invalid(form)

    def form_invalid(self, form):
        """:meta private:"""

        feature_name_4 = self.feature_type_texts.name_4

        error_message(self.request, _(f"Nepodařilo se uložit {feature_name_4}."))

        return super().form_invalid(form)

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()

        kwargs["feature_type"] = self.feature_type_texts.shortcut
        kwargs["person"] = self.get_person_with_permission_check()

        return kwargs


class FeatureAssignDeleteView(FeatureMixin, SuccessMessageMixin, DeleteView):
    """
    Unaasigns a feature from a person.

    **Success redirection view**: :class:`persons.views.PersonDetailView`

    **Permissions**:

    Users with the appropriate feature category permission.

    **Path parameters**:

    *   ``person`` - person ID
    *   ``pk`` - feature assignment ID
    """

    model = FeatureAssignment
    template_name = "features_assignment/delete.html"

    def get_success_url(self):
        """:meta private:"""

        return reverse("persons:detail", args=[self.person])

    def get_success_message(self, cleaned_data):
        """:meta private:"""

        return self.feature_type_texts.success_message_assigning_delete

    def get_context_data(self, **kwargs):
        """
        *   ``person``
        """

        kwargs.setdefault("person", self.get_person_with_permission_check())

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        """:meta private:"""

        if (
            hasattr(self.object, "transaction")
            and not self.object.transaction.is_settled
        ):
            self.object.transaction.delete()

        return super().form_valid(form)


class FeatureIndexView(FeatureMixin, ListView):
    """
    Displays a list of all features of a certain category.

    **Permissions**:

    Users with the appropriate feature category permission.

    **View parameters**:

    *   ``feature_type`` - feature category
    """

    context_object_name = "features"
    model = Feature
    template_name = "features/index.html"

    def get_queryset(self):
        """:meta private:"""

        feature_type_params = self.feature_type_texts
        return super().get_queryset().filter(feature_type=feature_type_params.shortcut)


class FeatureDetailView(FeatureMixin, DetailView):
    """
    Displays a detail of a feature of a certain category.

    **Permissions**:

    Users with the appropriate feature category permission.

    **View parameters**:

    *   ``feature_type`` - feature category

    **Path parameters**:

    *   ``pk`` - feature ID
    """

    model = Feature
    template_name = "features/detail.html"

    def get_context_data(self, **kwargs):
        """
        *   ``assignment_matrix`` - matrix of persons
            and their assignments of the feature
        """

        kwargs.setdefault("assignment_matrix", self._get_features_assignment_matrix())

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """:meta private:"""

        feature_type_params = self.feature_type_texts
        return super().get_queryset().filter(feature_type=feature_type_params.shortcut)

    def _get_features_assignment_matrix(self):
        """:meta private:"""

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
                    ).filter(Q(date_expire__isnull=True) | Q(date_expire__gte=today()))
                )
            )

            assigned_features = [f.is_assigned for f in features]

            if any(assigned_features):
                features_assignment_matrix["rows"].append(
                    {
                        "person": person,
                        "features": features,
                    }
                )

        return features_assignment_matrix


class FeatureEditView(FeatureMixin, MessagesMixin, UpdateView):
    """
    Creates or edits a feature of a certain category.

    **Success redirection view**: :class:`features.views.FeatureDetailView`

    **Permissions**:

    Users with the appropriate feature category permission.

    **View parameters**:

    *   ``feature_type`` - feature category

    **Path parameters**:

    *   ``pk``? - feature ID, necessary for editing
    """

    form_class = FeatureForm
    model = Feature
    template_name = "features/edit.html"
    error_message = _("Formulář se nepodařilo uložit. Opravte chyby a zkuste to znovu.")

    def get_object(self, queryset=None):
        """:meta private:"""

        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_success_url(self):
        """:meta private:"""

        return reverse(f"{self.feature_type}:detail", args=[self.object.pk])

    def get_success_message(self, cleaned_data):
        """:meta private:"""

        return self.feature_type_texts.success_message_save

    def form_valid(self, form):
        """:meta private:"""

        feature_type_texts = self.feature_type_texts

        form.instance.feature_type = feature_type_texts.shortcut

        return super().form_valid(form)

    def get_form(self, form_class=None):
        """:meta private:"""

        form = super().get_form(form_class)

        feature_type_texts = self.feature_type_texts

        if feature_type_texts.form_labels:
            for field, label in feature_type_texts.form_labels.items():
                if field in form.fields:
                    form.fields[field].label = label

        return form

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()

        kwargs["feature_type"] = self.feature_type_texts.shortcut

        return kwargs


class FeatureDeleteView(FeatureMixin, SuccessMessageMixin, DeleteView):
    """
    Deletes a feature of a certain category.

    **Success redirection view**: :class:`features.views.FeatureIndexView`

    **Permissions**:

    Users with the appropriate feature category permission.

    **View parameters**:

    *   ``feature_type`` - feature category

    **Path parameters**:

    *   ``pk`` - feature ID
    """

    model = Feature
    template_name = "features/delete.html"

    def get_success_url(self):
        """:meta private:"""

        return reverse(f"{self.feature_type}:index")

    def get_success_message(self, cleaned_data):
        """:meta private:"""

        return self.feature_type_texts.success_message_delete


class FeatureAssignToSelectedPersonView(FeatureMixin, SuccessMessageMixin, CreateView):
    """
    Assigns a feature of a certain category to a person.

    **Success redirection view**: :class:`features.views.FeatureDetailView`

    **Permissions**:

    Users with the appropriate feature category permission.

    **View parameters**:

    *   ``feature_type`` - feature category

    **Path parameters**:

    *   ``pk`` - feature ID

    **Request body parameters**:

    *   ``person``
    *   ``date_assigned``
    *   ``date_expire``
    *   ``date_returned``
    *   ``issuer``
    *   ``code``
    """

    form_class = FeatureAssignmentByFeatureForm
    model = FeatureAssignment
    success_message = _("Vlastnost byla úspěšně přiřazena.")
    template_name = "features_assignment/assign_to_selected_person.html"

    def dispatch(self, request, feature_type, pk, *args, **kwargs):
        """:meta private:"""

        self.feature = get_object_or_404(Feature, pk=pk)

        return super().dispatch(request, feature_type, pk, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        *   ``feature``
        """

        kwargs.setdefault("feature", self.feature)

        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()

        kwargs["feature"] = self.feature

        return kwargs

    def get_form(self, form_class=None):
        """:meta private:"""

        form = super().get_form(form_class)

        return extend_form_of_labels(form, self.feature_type_texts.form_labels)

    def get_success_url(self):
        """:meta private:"""

        return reverse(f"{self.feature_type}:detail", args=[self.feature.pk])

    def form_valid(self, form: FeatureAssignmentByFeatureForm):
        """:meta private:"""

        response = super().form_valid(form)

        form.add_transaction_if_necessary()

        return response
