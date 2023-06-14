from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import PersonForm, FeatureAssignmentForm
from .models import Person, FeatureAssignment

FEATURES_TYPES = {
    "qualifications": (
        "K",
        "kvalifikace",
        "kvalifikaci",
        "Kvalifikace byla osobě úspěšně přidána.",
        "Přiřazení kvalifikace bylo úspěšně upraveno.",
        "Daná osoba má již tuto kvalifikaci přiřazenou. Uložení se neprovedlo.",
        {
            "feature": "Název kvalifikace",
            "date_assigned": "Začátek platnost",
            "date_expire": "Konec platnosti",
        },
    ),
    "permissions": (
        "O",
        "oprávnění",
        "oprávnění",
        "Oprávnění bylo osobě úspěšně přidáno.",
        "Přiřazení oprávnění bylo úspěšně upraveno.",
        "Daná osoba má již toto oprávnění přiřazené. Uložení se neprovedlo.",
        {
            "feature": "Název oprávnění",
            "date_assigned": "Datum přiřazení",
            "date_expire": "Konec platnosti",
        },
    ),
    "equipments": (
        "V",
        "vybavení",
        "vybavení",
        "Vybavení bylo osobě úspěšně přidáno.",
        "Přiřazení vybavení bylo úspěšně upraveno.",
        "Daná osoba má již toto vybavení přiřazené. Uložení se neprovedlo.",
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
        context["type"] = FEATURES_TYPES[self.kwargs["feature_type"]][2]
        context["person"] = get_object_or_404(Person, id=self.kwargs["person"])
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if FEATURES_TYPES[self.kwargs["feature_type"]][6]:
            for field, label in FEATURES_TYPES[self.kwargs["feature_type"]][6].items():
                form.fields[field].label = label

        return form

    def form_valid(self, form):
        form.instance.person = get_object_or_404(Person, id=self.kwargs["person"])

        if not form.instance.pk:
            success_message = FEATURES_TYPES[self.kwargs["feature_type"]][3]
        else:
            success_message = FEATURES_TYPES[self.kwargs["feature_type"]][4]

        try:
            response = super().form_valid(form)
            messages.success(self.request, success_message)
            return response

        except IntegrityError:
            messages.error(self.request, FEATURES_TYPES[self.kwargs["feature_type"]][5])
            return super().form_invalid(form)

    def form_invalid(self, form):
        feature_name_4 = FEATURES_TYPES[self.kwargs["feature_type"]][2]
        messages.error(self.request, _(f"Nepodařilo se uložit {feature_name_4}."))

        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["feature_type"] = FEATURES_TYPES[self.kwargs["feature_type"]][0]
        return kwargs


class FeatureAssignDeleteView(SuccessMessageMixin, generic.edit.DeleteView):
    model = FeatureAssignment
    template_name = "persons/features_assignment_delete.html"

    def get_success_url(self):
        return reverse("persons:detail", args=[self.kwargs["person"]])

    def get_success_message(self, cleaned_data):
        feature_type_name_1 = FEATURES_TYPES[self.kwargs["feature_type"]][1]
        return f"{feature_type_name_1.capitalize()} byla úspěšně smazána."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["type"] = FEATURES_TYPES[self.kwargs["feature_type"]][2]
        context["person"] = get_object_or_404(Person, id=self.kwargs["person"])
        return context
