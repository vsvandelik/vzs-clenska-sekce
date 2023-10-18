from django.views import generic

from events.permissions import OccurrenceManagePermissionMixin
from events.views import (
    BulkApproveParticipantsMixin,
    EnrollMyselfParticipantMixin,
    EventCreateMixin,
    EventDetailBaseView,
    EventGeneratesDatesMixin,
    EventManagePermissionMixin,
    EventRestrictionMixin,
    EventUpdateMixin,
    InsertEventIntoContextData,
    InsertEventIntoModelFormKwargsMixin,
    InsertOccurrenceIntoContextData,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertPositionAssignmentIntoModelFormKwargs,
    ParticipantEnrollmentCreateMixin,
    ParticipantEnrollmentDeleteMixin,
    ParticipantEnrollmentUpdateMixin,
    RedirectToEventDetailOnFailureMixin,
    RedirectToEventDetailOnSuccessMixin,
)
from vzs.mixin_extensions import (
    InsertActivePersonIntoModelFormKwargsMixin,
    InsertRequestIntoModelFormKwargsMixin,
    MessagesMixin,
)

from .forms import (
    BulkAddOrganizerToOneTimeEventForm,
    BulkDeleteOrganizerFromOneTimeEventForm,
    OneTimeEventBulkApproveParticipantsForm,
    OneTimeEventEnrollMyselfOrganizerForm,
    OneTimeEventEnrollMyselfOrganizerOccurrenceForm,
    OneTimeEventEnrollMyselfParticipantForm,
    OneTimeEventForm,
    OneTimeEventParticipantEnrollmentForm,
    OneTimeEventUnenrollMyselfOrganizerForm,
    OneTimeEventUnenrollMyselfOrganizerOccurrenceForm,
    OrganizerOccurrenceAssignmentForm,
    TrainingCategoryForm,
)
from .models import OneTimeEventParticipantEnrollment, OrganizerOccurrenceAssignment
from .permissions import (
    OccurrenceEnrollOrganizerPermissionMixin,
    OccurrenceUnenrollOrganizerPermissionMixin,
    OneTimeEventEnrollOrganizerPermissionMixin,
    OneTimeEventUnenrollOrganizerPermissionMixin,
)


class OneTimeEventDetailView(EventDetailBaseView):
    template_name = "one_time_events/detail.html"

    def get_context_data(self, **kwargs):
        active_person = self.request.active_person
        kwargs.setdefault(
            "active_person_can_enroll_organizer",
            self.object.can_enroll_organizer(active_person),
        )
        kwargs.setdefault(
            "active_person_can_unenroll_organizer",
            self.object.can_unenroll_organizer(active_person),
        )
        kwargs.setdefault(
            "active_person_is_organizer", self.object.is_organizer(active_person)
        )
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


class EditTrainingCategoryView(
    EventManagePermissionMixin, MessagesMixin, EventRestrictionMixin, generic.UpdateView
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


class OrganizerForOccurrenceMixin(
    OccurrenceManagePermissionMixin, RedirectToEventDetailOnSuccessMixin, MessagesMixin
):
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
    EventManagePermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
):
    pass


class OrganizerSelectOccurrencesMixin:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("checked_occurrences", self.get_form().checked_occurrences())
        return super().get_context_data(**kwargs)


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

        OrganizerOccurrenceAssignment.objects.filter(
            person=person, occurrence__event=event
        ).delete()
        return super().form_valid(form)


class BulkAddOrganizerToOneTimeEventView(
    BulkCreateDeleteOrganizerMixin,
    OrganizerSelectOccurrencesMixin,
    generic.CreateView,
):
    form_class = BulkAddOrganizerToOneTimeEventForm
    template_name = "one_time_events/bulk_add_organizer.html"
    success_message = "Organizátor %(person)s přidán na vybrané dny"


class OneTimeEventBulkApproveParticipantsView(BulkApproveParticipantsMixin):
    form_class = OneTimeEventBulkApproveParticipantsForm
    template_name = "one_time_events/bulk_approve_participants.html"


class OneTimeEventEnrollMyselfOrganizerOccurrenceView(
    OccurrenceEnrollOrganizerPermissionMixin,
    RedirectToEventDetailOnFailureMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertOccurrenceIntoContextData,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
    InsertPositionAssignmentIntoModelFormKwargs,
    generic.CreateView,
):
    model = OrganizerOccurrenceAssignment
    form_class = OneTimeEventEnrollMyselfOrganizerOccurrenceForm
    success_message = "Přihlášení na organizátorskou pozici proběhlo úspěšně"


class OneTimeEventUnenrollMyselfOrganizerOccurrenceView(
    OccurrenceUnenrollOrganizerPermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    RedirectToEventDetailOnFailureMixin,
    generic.UpdateView,
):
    model = OrganizerOccurrenceAssignment
    form_class = OneTimeEventUnenrollMyselfOrganizerOccurrenceForm
    context_object_name = "assignment"
    success_message = "Odhlášení z organizátorské pozice proběhlo úspěšně"
    template_name = "one_time_events/modals/unenroll_myself_organizer_occurrence.html"


class OneTimeEventUnenrollMyselfOrganizerView(
    OneTimeEventUnenrollOrganizerPermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
    InsertRequestIntoModelFormKwargsMixin,
    generic.FormView,
):
    form_class = OneTimeEventUnenrollMyselfOrganizerForm
    template_name = "one_time_events/modals/unenroll_myself_organizer.html"
    success_message = "Odhlášení ze všech dnů události proběhlo úspěšně"

    def form_valid(self, form):
        form.cleaned_data["assignments_2_delete"].delete()
        return super().form_valid(form)


class OneTimeEventEnrollMyselfOrganizerView(
    OneTimeEventEnrollOrganizerPermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
    OrganizerSelectOccurrencesMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
    generic.CreateView,
):
    form_class = OneTimeEventEnrollMyselfOrganizerForm
    success_message = "Přihlášení jako organizátor proběhlo úspěšně"
    template_name = "one_time_events/enroll_myself_organizer.html"
