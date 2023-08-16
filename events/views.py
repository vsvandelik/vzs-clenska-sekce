from django.urls import reverse_lazy
from .models import (
    Event,
    EventPositionAssignment,
)
from persons.models import Person
from django.views import generic

from .forms import (
    EventAgeLimitForm,
    EventPositionAssignmentForm,
    EventGroupMembershipForm,
    EventAllowedPersonTypeForm,
)
from django.shortcuts import get_object_or_404, reverse
from vzs.mixin_extensions import MessagesMixin
from trainings.models import Training
from one_time_events.models import OneTimeEvent


class EventMixin:
    model = Event
    context_object_name = "event"


class RedirectToEventDetailOnSuccessMixin:
    def get_success_url(self):
        if hasattr(self, "object") and (
            type(self.object) is OneTimeEvent or type(self.object) is Training
        ):
            id = self.object.id
        elif "event_id" in self.kwargs:
            id = self.kwargs["event_id"]
        else:
            raise NotImplementedError

        event = Event.objects.get(pk=id)
        if isinstance(event, OneTimeEvent):
            viewname = "one_time_events:detail"
        elif isinstance(event, Training):
            viewname = "trainings:detail"
        else:
            raise NotImplementedError

        return reverse(viewname, args=[id])


class EventRestrictionMixin(RedirectToEventDetailOnSuccessMixin):
    model = Event


class EventCreateUpdateMixin(EventMixin, MessagesMixin, generic.FormView):
    success_url = reverse_lazy("events:index")


class EventCreateMixin(EventCreateUpdateMixin, generic.CreateView):
    success_message = "Událost %(name)s úspěšně přidána."


class EventUpdateMixin(EventCreateUpdateMixin, generic.UpdateView):
    success_message = "Událost %(name)s úspěšně upravena."


class EventGeneratesDatesMixin:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("dates", self.get_form().generate_dates())
        return super().get_context_data(**kwargs)


class PersonTypeDetailViewMixin:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("available_person_types", Person.Type.choices)
        kwargs.setdefault(
            "person_types_required",
            self.object.allowed_person_types.values_list("person_type", flat=True),
        )
        return super().get_context_data(**kwargs)


class EventDetailViewMixin(EventMixin, PersonTypeDetailViewMixin, generic.DetailView):
    def get_context_data(self, **kwargs):
        kwargs.setdefault(
            "event_position_assignments",
            EventPositionAssignment.objects.filter(event=self.object).all(),
        )
        return super().get_context_data(**kwargs)


class EventIndexView(EventMixin, generic.ListView):
    template_name = "events/index.html"
    context_object_name = "events"


class EventDeleteView(EventMixin, MessagesMixin, generic.DeleteView):
    template_name = "events/delete.html"
    success_url = reverse_lazy("events:index")

    def get_success_message(self, cleaned_data):
        return f"Událost {self.object.name} úspěšně smazána"


class EventPositionAssignmentMixin(MessagesMixin, RedirectToEventDetailOnSuccessMixin):
    model = EventPositionAssignment
    context_object_name = "position_assignment"


class EventPositionAssignmentCreateView(
    EventPositionAssignmentMixin, generic.CreateView
):
    template_name = "events/create_event_position_assignment.html"
    form_class = EventPositionAssignmentForm
    success_message = "Organizátorská pozice %(position)s přidána"

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=kwargs["event_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.event
        return kwargs


class EventPositionAssignmentUpdateView(
    EventPositionAssignmentMixin, generic.UpdateView
):
    template_name = "events/edit_event_position_assignment.html"
    success_message = "Organizátorská pozice %(position)s upravena"
    form_class = EventPositionAssignmentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["position"] = self.object.position
        kwargs["event"] = self.object.event
        return kwargs


class EventPositionAssignmentDeleteView(
    EventPositionAssignmentMixin, generic.DeleteView
):
    template_name = "events/delete_event_position_assignment.html"

    def get_success_message(self, cleaned_data):
        return f"Organizátorská pozice {self.object.position} smazána"


class EditAgeLimitView(MessagesMixin, EventRestrictionMixin, generic.UpdateView):
    template_name = "events/edit_age_limit.html"
    form_class = EventAgeLimitForm
    success_message = "Změna věkového omezení uložena"


class EditGroupMembershipView(MessagesMixin, EventRestrictionMixin, generic.UpdateView):
    template_name = "events/edit_group_membership.html"
    form_class = EventGroupMembershipForm
    success_message = "Změna vyžadování skupiny uložena"


class AddRemoveAllowedPersonTypeView(
    MessagesMixin, RedirectToEventDetailOnSuccessMixin, generic.UpdateView
):
    form_class = EventAllowedPersonTypeForm
    success_message = "Změna omezení pro typ členství uložena"
    model = Event

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = get_object_or_404(Event, pk=self.kwargs["pk"])
        return kwargs
