from django.shortcuts import reverse
from django.urls import reverse_lazy
from django.views import generic

from events.views import PersonTypeInsertIntoContextDataMixin
from features.models import Feature
from vzs.mixin_extensions import MessagesMixin
from .forms import (
    PositionForm,
    AddRemoveFeatureRequirementPositionForm,
    PositionAgeLimitForm,
    PositionGroupMembershipForm,
    PositionAllowedPersonTypeForm,
)
from .models import EventPosition


class PositionMixin:
    model = EventPosition
    context_object_name = "position"


class PositionCreateUpdateMixin(MessagesMixin, PositionMixin):
    template_name = "positions/create_edit.html"
    form_class = PositionForm

    def get_success_url(self):
        return reverse("positions:detail", args=[self.object.id])


class PositionModelFormWithoutFormMixin:
    def get_success_url(self):
        return reverse("positions:detail", args=[self.kwargs["pk"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = EventPosition.objects.get(pk=self.kwargs["pk"])
        return kwargs


class PositionIndexView(PositionMixin, generic.ListView):
    template_name = "positions/index.html"
    context_object_name = "positions"


class PositionCreateView(PositionCreateUpdateMixin, generic.CreateView):
    template_name = "positions/create.html"
    success_message = "Pozice %(name)s úspěšně přidána"


class PositionUpdateView(PositionCreateUpdateMixin, generic.UpdateView):
    template_name = "positions/edit.html"
    success_message = "Pozice %(name)s úspěšně upravena"


class PositionDeleteView(MessagesMixin, PositionMixin, generic.DeleteView):
    template_name = "positions/modals/delete.html"
    success_url = reverse_lazy("positions:index")

    def get_success_message(self, cleaned_data):
        return f"Pozice {self.object.name} úspěšně smazána"


class PositionDetailView(
    PositionMixin, PersonTypeInsertIntoContextDataMixin, generic.DetailView
):
    template_name = "positions/detail.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("qualifications", Feature.qualifications.all())
        kwargs.setdefault("permissions", Feature.permissions.all())
        kwargs.setdefault("equipment", Feature.equipments.all())
        return super().get_context_data(**kwargs)


class AddRemoveFeatureRequirementPositionView(
    PositionMixin, PositionModelFormWithoutFormMixin, MessagesMixin, generic.UpdateView
):
    form_class = AddRemoveFeatureRequirementPositionForm
    success_message = "Změna vyžadovaných features uložena"


class EditAgeLimitView(PositionMixin, MessagesMixin, generic.UpdateView):
    template_name = "events/edit_age_limit.html"
    form_class = PositionAgeLimitForm
    success_message = "Změna věkového omezení uložena"

    def get_success_url(self):
        return reverse("positions:detail", args=[self.object.id])


class EditGroupMembershipView(PositionMixin, MessagesMixin, generic.UpdateView):
    template_name = "events/edit_group_membership.html"
    form_class = PositionGroupMembershipForm
    success_message = "Změna členství ve skupině uložena"

    def get_success_url(self):
        return reverse("positions:detail", args=[self.object.id])


class AddRemoveAllowedPersonTypeToPositionView(
    PositionMixin, PositionModelFormWithoutFormMixin, MessagesMixin, generic.UpdateView
):
    form_class = PositionAllowedPersonTypeForm
    success_message = "Změna omezení na typ členství uložena"
