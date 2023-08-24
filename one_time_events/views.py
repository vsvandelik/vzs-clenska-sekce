from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import generic

from events.views import (
    EventCreateMixin,
    EventDetailViewMixin,
    EventUpdateMixin,
    EventGeneratesDatesMixin,
    EventRestrictionMixin,
    ParticipantEnrollmentCreateMixin,
    ParticipantEnrollmentUpdateMixin,
    ParticipantEnrollmentDeleteMixin,
    RedirectToEventDetailOnSuccessMixin,
)
from vzs.mixin_extensions import InsertRequestIntoModelFormKwargsMixin
from vzs.mixin_extensions import MessagesMixin
from .forms import (
    OneTimeEventForm,
    TrainingCategoryForm,
    OneTimeEventParticipantEnrollmentForm,
    OneTimeEventEnrollMyselfParticipantForm,
)
from .models import OneTimeEventParticipantEnrollment
from events.models import Event


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


class OneTimeEventParticipantEnrollmentCreateUpdateMixin:
    model = OneTimeEventParticipantEnrollment
    form_class = OneTimeEventParticipantEnrollmentForm


class OneTimeEventParticipantEnrollmentCreateView(
    OneTimeEventParticipantEnrollmentCreateUpdateMixin, ParticipantEnrollmentCreateMixin
):
    template_name = "one_time_events/create_participant_enrollment.html"


class OneTimeEventParticipantEnrollmentUpdateView(
    OneTimeEventParticipantEnrollmentCreateUpdateMixin, ParticipantEnrollmentUpdateMixin
):
    template_name = "one_time_events/edit_participant_enrollment.html"


class OneTimeEventParticipantEnrollmentDeleteView(ParticipantEnrollmentDeleteMixin):
    template_name = "one_time_events/delete_participant_enrollment.html"


class EnrollMyselfParticipantView(
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertRequestIntoModelFormKwargsMixin,
    generic.CreateView,
):
    model = OneTimeEventParticipantEnrollment
    form_class = OneTimeEventEnrollMyselfParticipantForm

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=self.kwargs["event_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.event
        return kwargs

    def form_invalid(self, form):
        super().form_invalid(form)
        return redirect("one_time_events:detail", pk=self.event.pk)


class UnenrollMyselfParticipantView(
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertRequestIntoModelFormKwargsMixin,
    generic.DeleteView,
):
    model = OneTimeEventParticipantEnrollment
    # form_class = OneTimeEventEnrollMyselfParticipantForm
    #
    # def dispatch(self, request, *args, **kwargs):
    #     self.event = get_object_or_404(Event, pk=self.kwargs["event_id"])
    #     return super().dispatch(request, *args, **kwargs)
    #
    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs["event"] = self.event
    #     return kwargs
    #
    # def form_invalid(self, form):
    #     super().form_invalid(form)
    #     return redirect("one_time_events:detail", pk=self.event.pk)
    #
