from django.shortcuts import render
from events.views import (
    EventCreateMixin,
    EventDetailViewMixin,
    EventUpdateMixin,
    EventGeneratesDatesMixin,
)
from django.views import generic
from .forms import OneTimeEventForm
from persons.models import Person
from django.shortcuts import get_object_or_404, redirect
from .models import OneTimeEvent
from .mixin_extensions import InsertRequestIntoModelFormKwargsMixin


class OneTimeEventDetailView(EventDetailViewMixin):
    template_name = "one_time_events/detail.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("persons", Person.objects.all())
        # kwargs.setdefault(
        #     "event_participation",
        #     EventOccurrenceParticipation.objects.filter(event=self.object).all(),
        # )
        # kwargs.setdefault(
        #     "event_participation_approved",
        #     EventOccurrenceParticipation.objects.filter(
        #         event=self.object, state=Participation.State.APPROVED
        #     ),
        # )
        # kwargs.setdefault(
        #     "event_participation_substitute",
        #     EventOccurrenceParticipation.objects.filter(
        #         event=self.object, state=Participation.State.SUBSTITUTE
        #     ),
        # )
        return super().get_context_data(**kwargs)


class OneTimeEventCreateView(
    InsertRequestIntoModelFormKwargsMixin, EventGeneratesDatesMixin, EventCreateMixin
):
    template_name = "one_time_events/create.html"
    form_class = OneTimeEventForm


class OneTimeEventUpdateView(
    InsertRequestIntoModelFormKwargsMixin, EventGeneratesDatesMixin, EventUpdateMixin
):
    template_name = "one_time_events/edit.html"
    form_class = OneTimeEventForm
