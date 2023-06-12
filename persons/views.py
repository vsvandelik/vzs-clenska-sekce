from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import IntegrityError
from django.http import HttpResponseNotFound, Http404
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import PersonForm, FeatureAssignmentForm, FeatureForm
from .models import Person, FeatureAssignment, Feature, FeatureTypeTexts


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
        self.feature_type_texts = None

    def get_success_url(self):
        return reverse("persons:detail", args=[self.kwargs["person"]])

    def get_context_data(self, **kwargs):
        context = super(FeatureAssignMixin, self).get_context_data(**kwargs)
        context["type"] = self.feature_type_texts.name_4

        try:
            context["person"] = Person.objects.get(id=self.kwargs["person"])
        except Person.DoesNotExist:
            raise Http404(_("Osoba nebyla nalezena."))

        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.feature_type_texts.form_labels:
            for field, label in self.feature_type_texts.form_labels.items():
                if field in form.fields:
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
                _(
                    f"{self.feature_type_texts.name_1.capitalize()} byla úspěšně přidána."
                ),
            )
            return response

        except IntegrityError:
            messages.error(
                self.request,
                _(
                    f"Nepodařilo se uložit {self.feature_type_texts.name_4}. Osoba již má danou {self.feature_type_texts.name_4} přiřazenou."
                ),
            )
            return super().form_invalid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, _(f"Nepodařilo se uložit {self.feature_type_texts.name_4}.")
        )

        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = self.feature_type_texts.shortcut
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
                _(
                    f"{self.feature_type_texts.name_1.capitalize()} byla úspěšně upravena."
                ),
            )
            return response

        except IntegrityError:
            messages.error(
                self.request,
                _(
                    f"Nepodařilo se uložit {self.feature_type_texts.name_4}. Osoba již má danou {self.feature_type_texts.name_4} přiřazenou."
                ),
            )
            return super().form_invalid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, _(f"Nepodařilo se uložit {self.feature_type_texts.name_4}.")
        )

        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = self.feature_type_texts.shortcut
        return kwargs


class FeatureAssignDeleteMixin(FeatureAssignMixin, generic.edit.DeleteView):
    model = FeatureAssignment
    template_name = "persons/features_assignment_delete.html"

    def form_valid(self, form):
        messages.success(
            self.request,
            _(f"{self.feature_type_texts.name_4.capitalize()} byla úspěšně smazána."),
        )
        return super().form_valid(form)


class QualificationAssignAddView(FeatureAssignAddMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type_texts = FeatureTypeTexts["qualifications"]


class QualificationAssignEditView(FeatureAssignEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type_texts = FeatureTypeTexts["qualifications"]


class QualificationAssignDeleteView(FeatureAssignDeleteMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type_texts = FeatureTypeTexts["qualifications"]


class PermissionAssignAddView(FeatureAssignAddMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type_texts = FeatureTypeTexts["permissions"]


class PermissionAssignEditView(FeatureAssignEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type_texts = FeatureTypeTexts["permissions"]


class PermissionAssignDeleteView(FeatureAssignDeleteMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type_texts = FeatureTypeTexts["permissions"]


class EquipmentAssignAddView(FeatureAssignAddMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type_texts = FeatureTypeTexts["equipment"]


class EquipmentAssignEditView(FeatureAssignEditMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type_texts = FeatureTypeTexts["equipment"]


class EquipmentAssignDeleteView(FeatureAssignDeleteMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature_type_texts = FeatureTypeTexts["equipment"]


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
    success_url = reverse_lazy("qualifications:index")
    success_message = "Kvalifikace byla úspěšně smazána."

    def get_template_names(self):
        return f"persons/{self.kwargs['feature_type']}_delete.html"

    def get_success_url(self):
        return reverse(f"{self.kwargs['feature_type']}:index")

    def get_success_message(self, cleaned_data):
        return FeatureTypeTexts[self.kwargs["feature_type"]].success_message_delete
