from datetime import datetime

from django.http import Http404
from django.utils import timezone
from django.views import generic

from events.models import EventOrOccurrenceState
from events.views import (
    EventCreateMixin,
    EventDetailBaseView,
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
    InsertPositionAssignmentIntoModelFormKwargs,
    OccurrenceDetailBaseView,
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    GetOccurrenceProvider,
)
from vzs.mixin_extensions import (
    InsertRequestIntoModelFormKwargsMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
)
from vzs.mixin_extensions import MessagesMixin
from .forms import (
    OneTimeEventForm,
    TrainingCategoryForm,
    OneTimeEventParticipantEnrollmentForm,
    OneTimeEventEnrollMyselfParticipantForm,
    OrganizerOccurrenceAssignmentForm,
    BulkDeleteOrganizerFromOneTimeEventForm,
    BulkAddOrganizerToOneTimeEventForm,
    OneTimeEventBulkApproveParticipantsForm,
    OneTimeEventEnrollMyselfOrganizerOccurrenceForm,
    OneTimeEventUnenrollMyselfOrganizerOccurrenceForm,
    OneTimeEventUnenrollMyselfOrganizerForm,
    OneTimeEventEnrollMyselfOrganizerForm,
    OneTimeEventFillAttendanceForm,
)
from .models import (
    OneTimeEventParticipantEnrollment,
    OrganizerOccurrenceAssignment,
    OneTimeEventOccurrence,
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


class OneTimeOccurrenceDetailView(OccurrenceDetailBaseView):
    model = OneTimeEventOccurrence
    template_name = "one_time_events_occurrences/detail.html"


class OneTimeEventOccurrenceAttendanceCanBeFilledMixin:
    def dispatch(self, request, *args, **kwargs):
        occurrence = self.get_object()
        if datetime.now(tz=timezone.get_default_timezone()).date() < occurrence.date:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class OccurrenceNotApprovedRestrictionMixin(GetOccurrenceProvider):
    def dispatch(self, request, *args, **kwargs):
        occurrence = super().get_occurrence(*args, **kwargs)
        if occurrence.state == EventOrOccurrenceState.COMPLETED:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class OneTimeEventFillAttendanceView(
    MessagesMixin,
    OneTimeEventOccurrenceAttendanceCanBeFilledMixin,
    RedirectToOccurrenceDetailOnSuccessMixin,
    OccurrenceNotApprovedRestrictionMixin,
    EventOccurrenceIdCheckMixin,
    InsertOccurrenceIntoContextData,
    InsertRequestIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
    generic.UpdateView,
):
    form_class = OneTimeEventFillAttendanceForm
    model = OneTimeEventOccurrence
    occurrence_id_key = "pk"
    success_message = "Zapsání docházky proběhlo úspěšně"
    template_name = "one_time_events_occurrences/attendance.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault(
            "participant_assignments", self.get_form().checked_participant_assignments()
        )
        kwargs.setdefault(
            "organizer_assignments", self.get_form().checked_organizer_assignments()
        )
        return super().get_context_data(**kwargs)
