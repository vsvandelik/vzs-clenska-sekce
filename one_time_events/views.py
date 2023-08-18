from events.views import (
    EventCreateMixin,
    EventDetailViewMixin,
    EventUpdateMixin,
    EventGeneratesDatesMixin,
    EventRestrictionMixin,
    RedirectToEventDetailOnSuccessMixin,
)
from vzs.mixin_extensions import InsertRequestIntoModelFormKwargsMixin
from .forms import (
    OneTimeEventForm,
    TrainingCategoryForm,
    OneTimeEventParticipantEnrollmentForm,
)
from .models import OneTimeEventParticipantEnrollment, OneTimeEvent
from django.views import generic
from django.shortcuts import get_object_or_404
from vzs.mixin_extensions import MessagesMixin


class OneTimeEventDetailView(EventDetailViewMixin):
    template_name = "one_time_events/detail.html"


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


class EditTrainingCategoryView(
    MessagesMixin, EventRestrictionMixin, generic.UpdateView
):
    template_name = "one_time_events/edit_training_category.html"
    form_class = TrainingCategoryForm
    success_message = "Změna vyžadování skupiny uložena"


class ParticipantEnrollmentCreateView(
    RedirectToEventDetailOnSuccessMixin, generic.CreateView
):
    model = OneTimeEventParticipantEnrollment
    context_object_name = "enrollment"
    form_class = OneTimeEventParticipantEnrollmentForm
    template_name = "one_time_events/create_participation_enrollment.html"

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(OneTimeEvent, pk=kwargs["event_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs.setdefault("event", self.event)
        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.event
        return kwargs
