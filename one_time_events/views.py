from django.shortcuts import get_object_or_404
from django.views import generic

from events.models import EventPositionAssignment
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
    InsertEventIntoContextData,
    BulkApproveParticipantsMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertOccurrenceIntoContextData,
    EnrollMyselfMixin,
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
    OneTimeEventBulkApproveParticipantsForm,
    OneTimeEventEnrollMyselfOrganizerOccurrenceForm,
)
from .models import (
    OneTimeEventParticipantEnrollment,
    OneTimeEventOccurrence,
    OrganizerOccurrenceAssignment,
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


class OrganizerForOccurrenceMixin(RedirectToEventDetailOnSuccessMixin, MessagesMixin):
    pass


class AddOrganizerForOccurrenceView(
    OrganizerForOccurrenceMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertOccurrenceIntoContextData,
    generic.CreateView,
):
    model = OrganizerOccurrenceAssignment
    form_class = OrganizerOccurrenceAssignmentForm
    template_name = "one_time_events/create_organizer_occurrence_assignment.html"
    success_message = "Organizátor %(person)s přidán"


class EditOrganizerForOccurrenceView(OrganizerForOccurrenceMixin, generic.UpdateView):
    model = OrganizerOccurrenceAssignment
    form_class = OrganizerOccurrenceAssignmentForm
    success_message = "Organizátor %(person)s upraven"
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


class DeleteOrganizerForOccurrenceView(OrganizerForOccurrenceMixin, generic.DeleteView):
    model = OrganizerOccurrenceAssignment
    template_name = "one_time_events/modals/delete_organizer_assignment.html"
    context_object_name = "organizer_assignment"

    def get_success_message(self, cleaned_data):
        return f"Organizátor {self.object.person} odebrán"


class BulkCreateDeleteOrganizerMixin(
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
):
    pass


class BulkDeleteOrganizerFromOneTimeEventView(
    BulkCreateDeleteOrganizerMixin,
    generic.FormView,
):
    form_class = BulkDeleteOrganizerFromOneTimeEventForm
    template_name = "one_time_events/bulk_delete_organizer.html"
    success_message = "Organizátor %(person)s úspěšně odebrán ze všech dnů"

    def form_valid(self, form):
        person = form.cleaned_data["person"]
        event = self.event

        organizer_assignments = OrganizerOccurrenceAssignment.objects.filter(
            person=person, occurrence__event=event
        )
        for organizer_assignment in organizer_assignments:
            organizer_assignment.delete()

        return super().form_valid(form)


class BulkAddOrganizerToOneTimeEventView(
    BulkCreateDeleteOrganizerMixin,
    generic.CreateView,
):
    form_class = BulkAddOrganizerFromOneTimeEventForm
    template_name = "one_time_events/bulk_add_organizer.html"
    success_message = "Organizátor %(person)s přidán na vybrané dny"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("checked_occurrences", self.get_form().checked_occurrences())
        return super().get_context_data(**kwargs)


class OneTimeEventBulkApproveParticipantsView(BulkApproveParticipantsMixin):
    form_class = OneTimeEventBulkApproveParticipantsForm
    template_name = "one_time_events/bulk_approve_participants.html"


class OneTimeEventEnrollMyselfOrganizerOccurrenceView(
    RedirectToEventDetailOnFailureMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertOccurrenceIntoContextData,
    EnrollMyselfMixin,
):
    model = OrganizerOccurrenceAssignment
    form_class = OneTimeEventEnrollMyselfOrganizerOccurrenceForm
    success_message = "TODO"

    def dispatch(self, request, *args, **kwargs):
        self.position_assignment = get_object_or_404(
            EventPositionAssignment, pk=self.kwargs["position_assignment_id"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["position_assignment"] = self.position_assignment
        return kwargs
