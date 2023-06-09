from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponseNotFound, Http404
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import PersonForm, FeatureAssignmentForm
from .models import Person, FeatureAssignment

FEATURES_TYPES = {
    "qualifications": ("K", "kvalifikace", "kvalifikaci"),
    "permissions": ("O", "oprávnění", "oprávnění"),
    "equipment": ("V", "vybavení", "vybavení"),
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
        ) = FEATURES_TYPES["qualifications"]


class QualificationAssignEditView(FeatureAssignEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
        ) = FEATURES_TYPES["qualifications"]


class QualificationAssignDeleteView(FeatureAssignDeleteMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
        ) = FEATURES_TYPES["qualifications"]


class PermissionAssignAddView(FeatureAssignAddMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
        ) = FEATURES_TYPES["permissions"]


class PermissionAssignEditView(FeatureAssignEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
        ) = FEATURES_TYPES["permissions"]


class PermissionAssignDeleteView(FeatureAssignDeleteMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
        ) = FEATURES_TYPES["permissions"]


class EquipmentAssignAddView(FeatureAssignAddMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
        ) = FEATURES_TYPES["equipment"]


class EquipmentAssignEditView(FeatureAssignEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
        ) = FEATURES_TYPES["equipment"]


class EquipmentAssignDeleteView(FeatureAssignDeleteMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (
            self.feature_type,
            self.feature_type_name_1,
            self.feature_type_name_4,
        ) = FEATURES_TYPES["equipment"]
