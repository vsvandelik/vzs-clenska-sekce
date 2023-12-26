from django.db.models import Q
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from events.models import ParticipantEnrollment
from events.permissions import (
    OccurrenceEnrollOrganizerPermissionMixin,
    OccurrenceManagePermissionMixin,
    OccurrenceUnenrollOrganizerPermissionMixin,
)
from events.views import (
    BulkApproveParticipantsMixin,
    EnrollMyselfParticipantMixin,
    EventCreateMixin,
    EventDetailBaseView,
    EventGeneratesDatesMixin,
    EventManagePermissionMixin,
    EventOccurrenceIdCheckMixin,
    EventRestrictionMixin,
    EventUpdateMixin,
    InsertEventIntoContextData,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoSelfObjectMixin,
    InsertOccurrenceIntoContextData,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertOccurrenceIntoSelfObjectMixin,
    InsertPositionAssignmentIntoModelFormKwargs,
    OccurrenceDetailBaseView,
    OccurrenceIsApprovedRestrictionMixin,
    OccurrenceIsClosedRestrictionMixin,
    OccurrenceNotApprovedRestrictionMixin,
    OccurrenceNotOpenedRestrictionMixin,
    OccurrenceOpenRestrictionMixin,
    ParticipantEnrollmentCreateMixin,
    ParticipantEnrollmentDeleteMixin,
    ParticipantEnrollmentUpdateMixin,
    RedirectToEventDetailOnFailureMixin,
    RedirectToEventDetailOnSuccessMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
)
from persons.models import Person, get_active_user
from vzs.mixin_extensions import (
    InsertActivePersonIntoModelFormKwargsMixin,
    InsertRequestIntoModelFormKwargsMixin,
    MessagesMixin,
)
from vzs.settings import GOOGLE_MAPS_API_KEY
from vzs.utils import date_pretty, export_queryset_csv, send_notification_email, today
from .forms import (
    ApproveOccurrenceForm,
    BulkAddOrganizerToOneTimeEventForm,
    BulkDeleteOrganizerFromOneTimeEventForm,
    CancelOccurrenceApprovementForm,
    OneTimeEventBulkApproveParticipantsForm,
    OneTimeEventCreateDuplicateForm,
    OneTimeEventEnrollMyselfOrganizerForm,
    OneTimeEventEnrollMyselfOrganizerOccurrenceForm,
    OneTimeEventEnrollMyselfParticipantForm,
    OneTimeEventFillAttendanceForm,
    OneTimeEventForm,
    OneTimeEventParticipantEnrollmentForm,
    OneTimeEventUnenrollMyselfOrganizerForm,
    OneTimeEventUnenrollMyselfOrganizerOccurrenceForm,
    OrganizerOccurrenceAssignmentForm,
    ReopenOneTimeEventOccurrenceForm,
    TrainingCategoryForm,
)
from .models import (
    OneTimeEvent,
    OneTimeEventAttendance,
    OneTimeEventOccurrence,
    OneTimeEventParticipantEnrollment,
    OrganizerOccurrenceAssignment,
)
from .permissions import (
    OccurrenceFillAttendancePermissionMixin,
    OccurrenceManagePermissionMixin2,
    OneTimeEventEnrollOrganizerPermissionMixin,
    OneTimeEventUnenrollOrganizerPermissionMixin,
)


class OneTimeEventDetailView(EventDetailBaseView):
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
        kwargs.setdefault(
            "active_person_participant_enrollment",
            self.object.get_participant_enrollment(active_person),
        )
        kwargs.setdefault("enrollment_states", ParticipantEnrollment.State)
        kwargs.setdefault(
            "map_is_available", GOOGLE_MAPS_API_KEY is not None and self.object.location
        )
        kwargs.setdefault("organizers_positions", self._get_organizers_table())

        return super().get_context_data(**kwargs)

    def get_template_names(self):
        active_person = self.request.active_person
        active_user = get_active_user(active_person)
        if self.object.can_user_manage(active_user):
            return "one_time_events/detail.html"
        else:
            return "one_time_events/detail_for_nonadmin.html"

    def _get_organizers_table(self):
        organizers_positions = []

        for position_assignment in self.object.position_assignments_sorted():
            max_length = 0
            organizers_per_occurrences = {}

            for occurrence in self.object.sorted_occurrences_list():
                organizer_assignments = OrganizerOccurrenceAssignment.objects.filter(
                    occurrence=occurrence, position_assignment=position_assignment
                )
                organizers_per_occurrences[occurrence] = organizer_assignments
                max_length = max(organizer_assignments.count(), max_length)

            organizers_positions.append(
                {
                    "name": position_assignment.position.name,
                    "position_assignment": position_assignment,
                    "count": max_length,
                    "organizers_per_occurrences": organizers_per_occurrences,
                }
            )

        return organizers_positions


class OneTimeEventListView(generic.ListView):
    template_name = "one_time_events/index.html"
    context_object_name = "events"

    def get_context_data(self, **kwargs):
        active_person = self.request.active_person
        user = get_active_user(active_person)

        enrolled_events_organizers = OrganizerOccurrenceAssignment.objects.filter(
            person_id=active_person
        ).values_list("occurrence__event", flat=True)
        enrolled_events_organizers = set(enrolled_events_organizers)

        enrolled_events = OneTimeEvent.objects.filter(
            Q(onetimeeventparticipantenrollment__person=active_person)
            | Q(pk__in=enrolled_events_organizers)
        ).distinct()

        for enrolled_event in enrolled_events:
            enrolled_event.active_person_enrollment = (
                enrolled_event.get_participant_enrollment(active_person)
            )

        visible_event_pks = [
            event.pk
            for event in OneTimeEvent.objects.all()
            if event.can_user_manage(user)
            or event.can_person_interact_with(active_person)
        ]

        available_events = OneTimeEvent.objects.filter(
            pk__in=visible_event_pks
        ).exclude(pk__in=enrolled_events)

        kwargs.setdefault("enrolled_events", enrolled_events)
        kwargs.setdefault("available_events", available_events)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return []


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


class OneTimeEventParticipantEnrollmentCreateUpdateMixin(
    EventManagePermissionMixin, InsertRequestIntoModelFormKwargsMixin
):
    model = OneTimeEventParticipantEnrollment
    form_class = OneTimeEventParticipantEnrollmentForm
    event_id_key = "event_id"


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

    def form_valid(self, form):
        enrollment = self.object
        if enrollment.state == ParticipantEnrollment.State.REJECTED:
            send_notification_email(
                _("Zrušení odmítnutí účasti"),
                _(
                    f"Na jednorázovou událost {enrollment.event} vám bylo umožněno znovu se přihlásit"
                ),
                [enrollment.person],
            )
        else:
            send_notification_email(
                _("Odstranění přihlášky"),
                _(
                    f"Vaše přihláška na jednorázovou událost {enrollment.event} byla smazána administrátorem"
                ),
                [enrollment.person],
            )
        return super().form_valid(form)


class OneTimeEventEnrollMyselfParticipantView(
    RedirectToEventDetailOnFailureMixin, EnrollMyselfParticipantMixin
):
    model = OneTimeEventParticipantEnrollment
    form_class = OneTimeEventEnrollMyselfParticipantForm
    template_name = "one_time_events/modals/enroll_waiting.html"
    success_message = "Přihlášení na událost proběhlo úspěšně"


class OrganizerForOccurrenceMixin(
    OccurrenceManagePermissionMixin,
    RedirectToEventDetailOnSuccessMixin,
    MessagesMixin,
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


class DeleteOrganizerForOccurrenceView(
    OccurrenceOpenRestrictionMixin, OrganizerForOccurrenceMixin, generic.DeleteView
):
    model = OrganizerOccurrenceAssignment
    template_name = "one_time_events/modals/delete_organizer_assignment.html"
    context_object_name = "organizer_assignment"

    def get_success_message(self, cleaned_data):
        return f"Organizátor {self.object.person} odebrán"

    def form_valid(self, form):
        assignment = self.object
        send_notification_email(
            _("Odhlášení z události"),
            _(
                f"Vaše přihláška na organizátorskou pozici dne {assignment.occurrence.date} události {assignment.occurrence.event} byla odstraněna administrátorem"
            ),
            [assignment.person],
        )
        return super().form_valid(form)


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

        send_notification_email(
            _("Odhlášení organizátora"),
            _(f"Byl(a) jste odhlášen jako organizátor ze všech dnů události {event}"),
            [person],
        )

        return super().form_valid(form)


class BulkAddOrganizerToOneTimeEventView(
    BulkCreateDeleteOrganizerMixin,
    OrganizerSelectOccurrencesMixin,
    generic.CreateView,
):
    form_class = BulkAddOrganizerToOneTimeEventForm
    template_name = "one_time_events/bulk_add_organizer.html"
    success_message = "Organizátor %(person)s přidán na vybrané dny"


class OneTimeEventBulkApproveParticipantsView(
    InsertRequestIntoModelFormKwargsMixin, BulkApproveParticipantsMixin
):
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

    def form_valid(self, form):
        assignment = form.instance
        send_notification_email(
            _("Odhlášení organizátora"),
            _(
                f"Byl(a) jste odhlášen jako organizátor dne události {assignment.occurrence.event}"
            ),
            [assignment.person],
        )

        return super().form_valid(form)


class OneTimeEventUnenrollMyselfOrganizerView(
    OneTimeEventUnenrollOrganizerPermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
    InsertActivePersonIntoModelFormKwargsMixin,
    generic.FormView,
):
    form_class = OneTimeEventUnenrollMyselfOrganizerForm
    template_name = "one_time_events/modals/unenroll_myself_organizer.html"
    success_message = "Odhlášení ze všech dnů události proběhlo úspěšně"

    def form_valid(self, form):
        form.cleaned_data["assignments_2_delete"].delete()

        send_notification_email(
            _("Odhlášení organizátora"),
            _(
                f"Byl(a) jste odhlášen jako organizátor ze všech dnů události {self.event}"
            ),
            [form.person],
        )

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


class OneTimeOccurrenceDetailView(OccurrenceDetailBaseView):
    model = OneTimeEventOccurrence
    template_name = "one_time_events_occurrences/detail.html"


class OneTimeEventOccurrenceAttendanceCanBeFilledMixin:
    def dispatch(self, request, *args, **kwargs):
        occurrence = self.get_object()
        if today() < occurrence.date:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class OneTimeEventFillAttendanceInsertAssignmentsIntoContextData:
    def get_context_data(self, **kwargs):
        kwargs.setdefault(
            "participant_assignments", self.get_form().checked_participant_assignments()
        )
        kwargs.setdefault(
            "organizer_assignments", self.get_form().checked_organizer_assignments()
        )
        return super().get_context_data(**kwargs)


class OneTimeEventFillAttendanceView(
    OccurrenceFillAttendancePermissionMixin,
    MessagesMixin,
    OneTimeEventFillAttendanceInsertAssignmentsIntoContextData,
    OneTimeEventOccurrenceAttendanceCanBeFilledMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
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


class ApproveOccurrenceView(
    OccurrenceManagePermissionMixin2,
    MessagesMixin,
    OneTimeEventFillAttendanceInsertAssignmentsIntoContextData,
    EventOccurrenceIdCheckMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    OccurrenceNotOpenedRestrictionMixin,
    InsertOccurrenceIntoContextData,
    InsertRequestIntoModelFormKwargsMixin,
    generic.UpdateView,
):
    form_class = ApproveOccurrenceForm
    model = OneTimeEventOccurrence
    occurrence_id_key = "pk"
    success_message = "Schválení proběhlo úspěšně"
    template_name = "one_time_events_occurrences/approve_occurrence.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("organizer_amounts", self.get_form().organizer_amounts())
        return super().get_context_data(**kwargs)


class ReopenOneTimeEventOccurrenceView(
    OccurrenceManagePermissionMixin2,
    MessagesMixin,
    OccurrenceIsClosedRestrictionMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    EventOccurrenceIdCheckMixin,
    InsertOccurrenceIntoContextData,
    generic.UpdateView,
):
    form_class = ReopenOneTimeEventOccurrenceForm
    model = OneTimeEventOccurrence
    occurrence_id_key = "pk"
    success_message = "Znovu otevření události a zrušení docházky proběhlo úspěšně"
    template_name = "one_time_events_occurrences/modals/reopen_occurrence.html"


class CancelOccurrenceApprovementView(
    OccurrenceManagePermissionMixin2,
    MessagesMixin,
    OccurrenceIsApprovedRestrictionMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    EventOccurrenceIdCheckMixin,
    InsertOccurrenceIntoContextData,
    generic.UpdateView,
):
    form_class = CancelOccurrenceApprovementForm
    model = OneTimeEventOccurrence
    occurrence_id_key = "pk"
    success_message = "Zrušení schválení proběhlo úspěšně"
    template_name = (
        "one_time_events_occurrences/modals/cancel_occurrence_approvement.html"
    )


class OneTimeEventOpenOccurrencesOverviewView(
    EventManagePermissionMixin, InsertEventIntoContextData, generic.TemplateView
):
    template_name = "one_time_events/modals/open_occurrences_overview.html"


class OneTimeEventClosedOccurrencesOverviewView(
    EventManagePermissionMixin, InsertEventIntoContextData, generic.TemplateView
):
    template_name = "one_time_events/modals/closed_occurrences_overview.html"


class OneTimeEventShowAttendanceView(
    EventManagePermissionMixin,
    MessagesMixin,
    InsertEventIntoContextData,
    generic.TemplateView,
):
    template_name = "one_time_events/detail_components/show_attendance.html"


class OneTimeEventExportParticipantsView(
    EventManagePermissionMixin, InsertEventIntoSelfObjectMixin, generic.View
):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        approved_participants_id = (
            self.event.onetimeeventparticipantenrollment_set.filter(
                state=ParticipantEnrollment.State.APPROVED
            ).values_list("person_id")
        )
        return export_queryset_csv(
            f"{self.event}_účastníci",
            Person.objects.filter(id__in=approved_participants_id),
        )


class OneTimeEventExportOrganizersView(
    EventManagePermissionMixin, InsertEventIntoSelfObjectMixin, generic.View
):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        organizers_id = OrganizerOccurrenceAssignment.objects.filter(
            occurrence__event=self.event
        ).values_list("person_id")
        return export_queryset_csv(
            f"{self.event}_organizátoři", Person.objects.filter(id__in=organizers_id)
        )


class OneTimeEventExportOrganizersOccurrenceView(
    OccurrenceManagePermissionMixin2,
    EventOccurrenceIdCheckMixin,
    InsertOccurrenceIntoSelfObjectMixin,
    generic.View,
):
    http_method_names = ["get"]
    occurrence_id_key = "pk"

    def get(self, request, *args, **kwargs):
        organizers_id = OrganizerOccurrenceAssignment.objects.filter(
            occurrence=self.occurrence, state=OneTimeEventAttendance.PRESENT
        ).values_list("person_id")
        return export_queryset_csv(
            f"{self.occurrence.event}_{date_pretty(self.occurrence.date)}_organizátoři",
            Person.objects.filter(id__in=organizers_id),
        )


class OneTimeEventCreateDuplicateView(
    EventManagePermissionMixin,
    MessagesMixin,
    generic.UpdateView,
    RedirectToEventDetailOnSuccessMixin,
):
    form_class = OneTimeEventCreateDuplicateForm
    model = OneTimeEvent

    def form_valid(self, form):
        instance = form.instance
        new_event = instance.duplicate()

        for position_assignment in instance.eventpositionassignment_set.all():
            position_assignment.duplicate(new_event)

        for occurrence in instance.eventoccurrence_set.all():
            occurrence.duplicate(new_event)

        self.event_id = new_event.id
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("one_time_events:edit-duplicate", args=[self.event_id])


class OneTimeEventUpdateDuplicateView(
    InsertRequestIntoModelFormKwargsMixin,
    EventGeneratesDatesMixin,
    EventUpdateMixin,
    RedirectToEventDetailOnSuccessMixin,
):
    template_name = "one_time_events/edit_duplicate.html"
    form_class = OneTimeEventForm
