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
from .permissions import PositionPermissionMixin


class PositionMixin(PositionPermissionMixin):
    context_object_name = "position"
    model = EventPosition


class PositionCreateUpdateMixin(MessagesMixin, PositionMixin):
    form_class = PositionForm
    template_name = "positions/create_edit.html"


class PositionIndexView(PositionMixin, ListView):
    context_object_name = "positions"
    template_name = "positions/index.html"


class PositionCreateView(PositionCreateUpdateMixin, CreateView):
    success_message = "Pozice %(name)s úspěšně přidána"
    template_name = "positions/create.html"


class PositionUpdateView(PositionCreateUpdateMixin, UpdateView):
    success_message = "Pozice %(name)s úspěšně upravena"
    template_name = "positions/edit.html"


class PositionDeleteView(MessagesMixin, PositionMixin, DeleteView):
    success_url = reverse_lazy("positions:index")
    template_name = "positions/modals/delete.html"

    def get_success_message(self, cleaned_data):
        return f"Pozice {self.object.name} úspěšně smazána"

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            position = self.get_object()

            if position.events_using().exists():
                raise Http404("Tato stránka není dostupná")

        return super().dispatch(request, *args, **kwargs)


class PositionDetailView(
    PositionMixin, PersonTypeInsertIntoContextDataMixin, DetailView
):
    template_name = "positions/detail.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault(
            "qualifications", Feature.qualifications.filter(assignable=True)
        )
        kwargs.setdefault("permissions", Feature.permissions.filter(assignable=True))
        kwargs.setdefault("equipment", Feature.equipments.filter(assignable=True))
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
    form_class = PositionAgeLimitForm
    template_name = "events/edit_age_limit.html"
    success_message = "Změna věkového omezení uložena"


class EditGroupMembershipView(PositionMixin, MessagesMixin, UpdateView):
    form_class = PositionGroupMembershipForm
    success_message = "Změna členství ve skupině uložena"
    template_name = "events/edit_group_membership.html"


class AddRemoveAllowedPersonTypeToPositionView(
    PositionMixin, MessagesMixin, UpdateView
):
    form_class = PositionAllowedPersonTypeForm
    success_message = "Změna omezení na typ členství uložena"
