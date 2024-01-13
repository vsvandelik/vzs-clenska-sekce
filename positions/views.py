from django.http import Http404, HttpResponseRedirect
from django.urls import reverse_lazy, resolve, reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from events.views import PersonTypeInsertIntoContextDataMixin
from features.models import Feature
from vzs.mixins import MessagesMixin

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
    """:meta private:"""

    context_object_name = "position"
    model = EventPosition


class PositionCreateUpdateMixin(MessagesMixin, PositionMixin):
    """:meta private:"""

    form_class = PositionForm
    template_name = "positions/create_edit.html"


class PositionIndexView(PositionMixin, ListView):
    """
    Displays the list of all positions.

    **Permissions:**

    Users who manage any event category.
    """

    context_object_name = "positions"
    ordering = ["name"]
    template_name = "positions/index.html"


class PositionCreateView(PositionCreateUpdateMixin, CreateView):
    """
    Creates a new position.

    **Success redirection view**: :class:`PositionDetailView`

    **Permissions:**

    Users who manage any event category.

    **Request body parameters:**

    *   ``name``
    *   ``wage_hour``
    """

    success_message = "Pozice %(name)s úspěšně přidána"
    template_name = "positions/create.html"


class PositionUpdateView(PositionCreateUpdateMixin, UpdateView):
    """
    Edits a position.

    **Success redirection view**: :class:`PositionDetailView`

    **Permissions:**

    Users who manage any event category.

    **Path parameters:**

    *   ``pk`` - position ID

    **Request body parameters:**

    *   ``name``
    *   ``wage_hour``
    """

    success_message = "Pozice %(name)s úspěšně upravena"
    template_name = "positions/edit.html"


class PositionDeleteView(MessagesMixin, PositionMixin, DeleteView):
    """
    Deletes a position.

    **Success redirection view**: :class:`PositionIndexView`

    **Permissions:**

    Users who manage any event category.

    **Path parameters:**

    *   ``pk`` - position ID
    """

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
    """
    Displays a detail of a position.

    **Permissions:**

    Users who manage any event category.

    **Path parameters:**

    *   ``pk`` - position ID
    """

    template_name = "positions/detail.html"

    def get_context_data(self, **kwargs):
        """
        *  ``qualifications`` - assignable qualifications
        *  ``permissions`` - assignable permissions
        *  ``equipment`` - assignable equipment
        """

        kwargs.setdefault(
            "qualifications", Feature.qualifications.filter(assignable=True)
        )
        kwargs.setdefault("permissions", Feature.permissions.filter(assignable=True))
        kwargs.setdefault("equipment", Feature.equipments.filter(assignable=True))
        return super().get_context_data(**kwargs)


class AddRemoveFeatureRequirementPositionMixin(
    PositionMixin, MessagesMixin, UpdateView
):
    """:meta private:"""

    success_message = "Změna vyžadovaných features uložena"

    def form_invalid(self, form):
        super().form_invalid(form)

        return HttpResponseRedirect(
            reverse("positions:detail", kwargs={"pk": self.object.pk})
        )


class AddFeatureRequirementPositionView(AddRemoveFeatureRequirementPositionMixin):
    """
    Adds a feature requirement to a position.

    **Success redirection view**: :class:`PositionDetailView`

    **Permissions:**

    Users who manage any event category.

    **Path parameters:**

    *   ``pk`` - position ID

    **Request body parameters:**

    *   ``feature`` - feature ID
    """

    form_class = AddFeatureRequirementPositionForm


class RemoveFeatureRequirementPositionView(AddRemoveFeatureRequirementPositionMixin):
    """
    Removes a feature requirement from a position.

    **Success redirection view**: :class:`PositionDetailView`

    **Permissions:**

    Users who manage any event category.

    **Path parameters:**

    *   ``pk`` - position ID

    **Request body parameters:**

    *   ``feature`` - feature ID
    """

    form_class = RemoveFeatureRequirementPositionForm


class EditAgeLimitView(PositionMixin, MessagesMixin, UpdateView):
    """
    Edits the age limit of a position.

    **Success redirection view**: :class:`PositionDetailView`

    **Permissions:**

    Users who manage any event category.

    **Path parameters:**

    *   ``pk`` - position ID

    **Request body parameters:**

    *   ``min_age``
    *   ``max_age``
    """

    form_class = PositionAgeLimitForm
    success_message = "Změna věkového omezení uložena"
    template_name = "events/edit_age_limit.html"


class EditGroupMembershipView(PositionMixin, MessagesMixin, UpdateView):
    """
    Edits the group requirement of a position.

    **Success redirection view**: :class:`PositionDetailView`

    **Permissions:**

    Users who manage any event category.

    **Path parameters:**

    *   ``pk`` - position ID

    **Request body parameters:**

    *   ``group``
    """

    form_class = PositionGroupMembershipForm
    success_message = "Změna členství ve skupině uložena"
    template_name = "events/edit_group_membership.html"


class AddRemoveAllowedPersonTypeToPositionView(
    PositionMixin, MessagesMixin, UpdateView
):
    """
    Flips the required person type of a position.

    **Success redirection view**: :class:`PositionDetailView`

    **Permissions:**

    Users who manage any event category.

    **Path parameters:**

    *   ``pk`` - position ID

    **Request body parameters:**

    *   ``person_type``
    """

    form_class = PositionAllowedPersonTypeForm
    success_message = "Změna omezení na typ členství uložena"
