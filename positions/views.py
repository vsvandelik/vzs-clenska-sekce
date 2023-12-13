from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from events.views import PersonTypeInsertIntoContextDataMixin
from features.models import Feature
from vzs.mixin_extensions import MessagesMixin

from .forms import (
    AddFeatureRequirementPositionForm,
    PositionAgeLimitForm,
    PositionAllowedPersonTypeForm,
    PositionForm,
    PositionGroupMembershipForm,
    RemoveFeatureRequirementPositionForm,
)
from .models import EventPosition


class PositionMixin:
    model = EventPosition
    context_object_name = "position"


class PositionCreateUpdateMixin(MessagesMixin, PositionMixin):
    template_name = "positions/create_edit.html"
    form_class = PositionForm


class PositionIndexView(PositionMixin, ListView):
    template_name = "positions/index.html"
    context_object_name = "positions"


class PositionCreateView(PositionCreateUpdateMixin, CreateView):
    template_name = "positions/create.html"
    success_message = "Pozice %(name)s úspěšně přidána"


class PositionUpdateView(PositionCreateUpdateMixin, UpdateView):
    template_name = "positions/edit.html"
    success_message = "Pozice %(name)s úspěšně upravena"


class PositionDeleteView(MessagesMixin, PositionMixin, DeleteView):
    template_name = "positions/modals/delete.html"
    success_url = reverse_lazy("positions:index")

    def get_success_message(self, cleaned_data):
        return f"Pozice {self.object.name} úspěšně smazána"

    def dispatch(self, request, *args, **kwargs):
        position = self.get_object()

        if position.events_using().exists():
            raise Http404("Tato stránka není dostupná")

        return super().dispatch(request, *args, **kwargs)


class PositionDetailView(
    PositionMixin, PersonTypeInsertIntoContextDataMixin, DetailView
):
    template_name = "positions/detail.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("qualifications", Feature.qualifications.all())
        kwargs.setdefault("permissions", Feature.permissions.all())
        kwargs.setdefault("equipment", Feature.equipments.all())

        return super().get_context_data(**kwargs)


class AddRemoveFeatureRequirementPositionMixin(
    PositionMixin, MessagesMixin, UpdateView
):
    success_message = "Změna vyžadovaných features uložena"


class AddFeatureRequirementPositionView(AddRemoveFeatureRequirementPositionMixin):
    form_class = AddFeatureRequirementPositionForm


class RemoveFeatureRequirementPositionView(AddRemoveFeatureRequirementPositionMixin):
    form_class = RemoveFeatureRequirementPositionForm


class EditAgeLimitView(PositionMixin, MessagesMixin, UpdateView):
    template_name = "events/edit_age_limit.html"
    form_class = PositionAgeLimitForm
    success_message = "Změna věkového omezení uložena"


class EditGroupMembershipView(PositionMixin, MessagesMixin, UpdateView):
    template_name = "events/edit_group_membership.html"
    form_class = PositionGroupMembershipForm
    success_message = "Změna členství ve skupině uložena"


class AddRemoveAllowedPersonTypeToPositionView(
    PositionMixin, MessagesMixin, UpdateView
):
    form_class = PositionAllowedPersonTypeForm
    success_message = "Změna omezení na typ členství uložena"
