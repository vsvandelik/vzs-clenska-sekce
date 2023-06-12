from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import IntegrityError
from django.http import HttpResponseNotFound, Http404
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import PersonForm, FeatureAssignmentForm, FeatureForm
from .models import Person, FeatureAssignment, Feature

FEATURES_TYPES = {
    "qualifications": (
        "K",
        "kvalifikace",
        "kvalifikaci",
        {
            "feature": "Název kvalifikace",
            "date_assigned": "Začátek platnost",
            "date_expire": "Konec platnosti",
            "parent": "Nadřazená kategorie",
            "name": "Název kvalifikace",
            "never_expires": "Neomezená platnost",
        },
    ),
    "permissions": (
        "O",
        "oprávnění",
        "oprávnění",
        {
            "feature": "Název oprávnění",
            "date_assigned": "Datum přiřazení",
            "date_expire": "Konec platnosti",
        },
    ),
    "equipment": (
        "V",
        "vybavení",
        "vybavení",
        {
            "feature": "Název vybavení",
            "date_assigned": "Datum zapůjčení",
            "date_expire": "Datum vrácení",
        },
    ),
}


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
            person=self.kwargs["pk"], feature__feature_type="K"
        )
        context["permissions"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"], feature__feature_type="O"
        )
        context["equipments"] = FeatureAssignment.objects.filter(
            person=self.kwargs["pk"], feature__feature_type="V"
        )
        return context


class PersonCreateView(generic.edit.CreateView):
    model = Person
    template_name = "persons/edit.html"
    form_class = PersonForm


class PersonUpdateView(generic.edit.UpdateView):
    model = Person
    template_name = "persons/edit.html"
    form_class = PersonForm


class PersonDeleteView(generic.edit.DeleteView):
    model = Person
    template_name = "persons/confirm_delete.html"
    success_url = reverse_lazy("persons:index")


class FeatureAssignMixin(generic.edit.FormMixin):
    model = FeatureAssignment

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type = None
        self.feature_type_name_1 = None
        self.feature_type_name_4 = None
        self.labels = None

    def get_success_url(self):
        return reverse("persons:detail", args=[self.kwargs["person"]])

    def get_context_data(self, **kwargs):
        context = super(FeatureAssignMixin, self).get_context_data(**kwargs)
        context["type"] = self.feature_type_name_4

        try:
            context["person"] = Person.objects.get(id=self.kwargs["person"])
        except Person.DoesNotExist:
            raise Http404(_("Osoba nebyla nalezena."))

        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.labels:
            for field, label in self.labels.items():
                form.fields[field].label = label

        return form


class FeatureAssignAddMixin(FeatureAssignMixin, generic.edit.CreateView):
    form_class = FeatureAssignmentForm
    template_name = "persons/features_assignment_edit.html"

    def form_valid(self, form):
        try:
            form.instance.person = Person.objects.get(id=self.kwargs["person"])
        except Person.DoesNotExist:
            return HttpResponseNotFound(_("Osoba nebyla nalezena."))

        try:
            response = super().form_valid(form)
            messages.success(
                self.request,
                _(f"{self.feature_type_name_1.capitalize()} byla úspěšně přidána."),
            )
            return response

        except IntegrityError:
            messages.error(
                self.request,
                _(
                    f"Nepodařilo se uložit {self.feature_type_name_4}. Osoba již má danou {self.feature_type_name_4} přiřazenou."
                ),
            )
            return super().form_invalid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, _(f"Nepodařilo se uložit {self.feature_type_name_4}.")
        )

        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = self.feature_type
        return kwargs


class FeatureAssignEditMixin(FeatureAssignMixin, generic.edit.UpdateView):
    form_class = FeatureAssignmentForm
    template_name = "persons/features_assignment_edit.html"

    def form_valid(self, form):
        try:
            form.instance.person = Person.objects.get(id=self.kwargs["person"])
        except Person.DoesNotExist:
            return HttpResponseNotFound(_("Osoba nebyla nalezena."))

        try:
            response = super().form_valid(form)
            messages.success(
                self.request,
                _(f"{self.feature_type_name_1.capitalize()} byla úspěšně upravena."),
            )
            return response

        except IntegrityError:
            messages.error(
                self.request,
                _(
                    f"Nepodařilo se uložit {self.feature_type_name_4}. Osoba již má danou {self.feature_type_name_4} přiřazenou."
                ),
            )
            return super().form_invalid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, _(f"Nepodařilo se uložit {self.feature_type_name_4}.")
        )

        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = self.feature_type
        return kwargs


class FeatureAssignDeleteMixin(FeatureAssignMixin, generic.edit.DeleteView):
    model = FeatureAssignment
    template_name = "persons/features_assignment_delete.html"

    def form_valid(self, form):
        messages.success(
            self.request,
            _(f"{self.feature_type_name_1.capitalize()} byla úspěšně smazána."),
        )
        return super().form_valid(form)


class QualificationAssignAddView(FeatureAssignAddMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
            self.labels,
        ) = FEATURES_TYPES["qualifications"]


class QualificationAssignEditView(FeatureAssignEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
            self.labels,
        ) = FEATURES_TYPES["qualifications"]


class QualificationAssignDeleteView(FeatureAssignDeleteMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
            self.labels,
        ) = FEATURES_TYPES["qualifications"]


class PermissionAssignAddView(FeatureAssignAddMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
            self.labels,
        ) = FEATURES_TYPES["permissions"]


class PermissionAssignEditView(FeatureAssignEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
            self.labels,
        ) = FEATURES_TYPES["permissions"]


class PermissionAssignDeleteView(FeatureAssignDeleteMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
            self.labels,
        ) = FEATURES_TYPES["permissions"]


class EquipmentAssignAddView(FeatureAssignAddMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
            self.labels,
        ) = FEATURES_TYPES["equipment"]


class EquipmentAssignEditView(FeatureAssignEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
            self.labels,
        ) = FEATURES_TYPES["equipment"]


class EquipmentAssignDeleteView(FeatureAssignDeleteMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
            self.labels,
        ) = FEATURES_TYPES["equipment"]


class QualificationIndex(generic.ListView):
    model = Feature
    template_name = "persons/qualifications_index.html"
    context_object_name = "qualifications"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(feature_type=FEATURES_TYPES["qualifications"][0])
        )


class QualificationDetail(generic.DetailView):
    model = Feature
    template_name = "persons/qualifications_detail.html"
    context_object_name = "qualification"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(feature_type=FEATURES_TYPES["qualifications"][0])
        )


class QualificationEdit(generic.edit.UpdateView):
    model = Feature
    form_class = FeatureForm
    template_name = "persons/qualifications_edit.html"
    feature_type, feature_type_name_1, feature_type_name_4, labels = FEATURES_TYPES[
        "qualifications"
    ]

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None

    def get_success_url(self):
        return reverse("qualifications:detail", args=(self.object.pk,))

    def form_valid(self, form):
        form.instance.feature_type = self.feature_type
        messages.success(self.request, _("Kvalifikace byla úspěšně uložena."))
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.labels:
            for field, label in self.labels.items():
                if field in form.fields:
                    form.fields[field].label = label

        return form


class QualificationDelete(SuccessMessageMixin, generic.edit.DeleteView):
    model = Feature
    template_name = "persons/qualifications_delete.html"
    success_url = reverse_lazy("qualifications:index")
    success_message = "Kvalifikace byla úspěšně smazána."
