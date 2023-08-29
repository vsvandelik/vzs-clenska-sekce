from django.shortcuts import get_object_or_404
from django.views import generic

from events.models import Event
from events.views import (
    EventCreateMixin,
    EventDetailViewMixin,
    EventUpdateMixin,
    EventGeneratesDatesMixin,
    EventRestrictionMixin,
    ParticipantEnrollmentCreateMixin,
    ParticipantEnrollmentUpdateMixin,
    ParticipantEnrollmentDeleteMixin,
    EnrollMyselfParticipantMixin,
    RedirectToEventDetailOnFailureMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertEventIntoModelFormKwargsMixin,
)
from vzs.mixin_extensions import InsertRequestIntoModelFormKwargsMixin
from vzs.mixin_extensions import MessagesMixin
from .forms import (
    OneTimeEventForm,
    TrainingCategoryForm,
    OneTimeEventParticipantEnrollmentForm,
    OneTimeEventEnrollMyselfParticipantForm,
    OrganizerOccurrenceAssignmentForm,
    BulkDeleteOrganizerFromOneTimeEventForm,
    BulkAddOrganizerFromOneTimeEventForm,
)
from .models import (
    OneTimeEventParticipantEnrollment,
    OneTimeEventOccurrence,
    OrganizerOccurrenceAssignment,
    OneTimeEvent,
)


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
    template_name = "one_time_events/modals/delete_participant_enrollment.html"


class OneTimeEventEnrollMyselfParticipantView(
    RedirectToEventDetailOnFailureMixin, EnrollMyselfParticipantMixin
):
    model = OneTimeEventParticipantEnrollment
    form_class = OneTimeEventEnrollMyselfParticipantForm
    template_name = "one_time_events/modals/enroll_waiting.html"
    success_message = "Přihlášení na událost proběhlo úspěšně"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("event", self.event)
        return super().get_context_data(**kwargs)


class AddOrganizerForOccurrenceView(
    RedirectToEventDetailOnSuccessMixin, generic.CreateView
):
    model = OrganizerOccurrenceAssignment
    form_class = OrganizerOccurrenceAssignmentForm
    template_name = "one_time_events/create_organizer_occurrence_assignment.html"

    def dispatch(self, request, *args, **kwargs):
        self.occurrence = get_object_or_404(
            OneTimeEventOccurrence, pk=self.kwargs["occurrence_id"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["occurrence"] = self.occurrence
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs.setdefault("occurrence", self.occurrence)
        kwargs.setdefault("event", self.occurrence.event)
        return super().get_context_data(**kwargs)


class EditOrganizerForOccurrenceView(
    RedirectToEventDetailOnSuccessMixin, generic.UpdateView
):
    model = OrganizerOccurrenceAssignment
    form_class = OrganizerOccurrenceAssignmentForm
    template_name = "one_time_events/edit_organizer_occurrence_assignment.html"
    context_object_name = "organizer_assignment"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["occurrence"] = self.object.occurrence
        kwargs["person"] = self.object.person
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs.setdefault("occurrence", self.object.occurrence)
        kwargs.setdefault("event", self.object.occurrence.event)
        return super().get_context_data(**kwargs)


class DeleteOrganizerForOccurrenceView(
    RedirectToEventDetailOnSuccessMixin, generic.DeleteView
):
    model = OrganizerOccurrenceAssignment
    template_name = "one_time_events/modals/delete_organizer_assignment.html"
    context_object_name = "organizer_assignment"


class BulkDeleteOrganizerFromOneTimeEvent(
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertEventIntoModelFormKwargsMixin,
    generic.FormView,
):
    model = OneTimeEvent
    form_class = BulkDeleteOrganizerFromOneTimeEventForm
    template_name = "one_time_events/bulk_delete_organizer.html"
    success_message = "Organizátor %(person)s úspěšně odebrán ze všech dnů"

    def form_valid(self, form):
        person = form.cleaned_data["person"]
        event = form.cleaned_data["event"]

        organizer_assignments = OrganizerOccurrenceAssignment.objects.filter(
            person=person, occurrence__event=event
        )
        for organizer_assignment in organizer_assignments:
            organizer_assignment.delete()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs.setdefault("event", self.event)
        return super().get_context_data(**kwargs)


class BulkAddOrganizerToOneTimeEvent(
    RedirectToEventDetailOnSuccessMixin,
    InsertEventIntoModelFormKwargsMixin,
    generic.CreateView,
):
    model = OneTimeEvent
    form_class = BulkAddOrganizerFromOneTimeEventForm
    template_name = "one_time_events/bulk_add_organizer.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("event", self.event)
        return super().get_context_data(**kwargs)
