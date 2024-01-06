from django.db.models import Q
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from events.models import EventOrOccurrenceState, ParticipantEnrollment
from events.permissions import (
    OccurrenceEnrollOrganizerPermissionMixin,
    OccurrenceManagePermissionMixinID,
    OccurrenceUnenrollOrganizerPermissionMixin,
)
from events.views import (
    BulkApproveParticipantsMixin,
    EnrollMyselfParticipantMixin,
    EventAdminListMixin,
    EventCreateMixin,
    EventDetailMixin,
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
from users.permissions import LoginRequiredMixin
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
    OneTimeEventsFilterForm,
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
    OccurrenceManagePermissionMixinPK,
    OneTimeEventCreatePermissionMixin,
    OneTimeEventEnrollOrganizerPermissionMixin,
    OneTimeEventUnenrollOrganizerPermissionMixin,
)


class OneTimeEventDetailView(EventDetailMixin):
    """
    Displays the detail of a one-time event.

    **Permissions**:

    Users that can manage the event or interact with it.

    **Path parameters:**

    *   ``pk`` - event ID
    """

    def get_context_data(self, **kwargs):
        """
        *   ``active_person_can_enroll_organizer``: whether the active person
            can enroll as an organizer of the event
        *   ``active_person_can_unenroll_organizer``: whether the active person
            can unenroll as organizer of the event
        *   ``active_person_is_organizer``: whether the active person
            is currently enrolled as an organizer of the event
        *   ``active_person_participant_enrollment``: the active person's
            participant enrollment
        *   ``enrollment_states``: the values of ``ParticipantEnrollment.State``
        *   ``map_is_available``: whether the embedded Google map is available
        *   ``organizers_positions``: the organizers positions info
        """

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
        """:meta private:"""

        active_person = self.request.active_person
        active_user = get_active_user(active_person)
        if self.object.can_user_manage(active_user):
            return "one_time_events/detail.html"
        else:
            return "one_time_events/detail_for_nonadmin.html"

    def _get_organizers_table(self):
        """:meta private:"""

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


class OneTimeEventListView(LoginRequiredMixin, generic.ListView):
    """
    Displays the list of one-time events relevant to the active person.

    **Permissions**:

    Any logged-in user.
    """

    context_object_name = "events"
    template_name = "one_time_events/index.html"

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

        self._add_upcoming_events_participant_kwargs(kwargs)
        self._add_upcoming_events_organizer_kwargs(kwargs)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """:meta private:"""

        return []

    def _add_upcoming_events_participant_kwargs(self, kwargs):
        """:meta private:"""

        active_person = self.request.active_person

        enrolled_events = OneTimeEvent.get_upcoming_by_participant(active_person)
        for enrolled_event in enrolled_events:
            enrolled_event.enrollment = enrolled_event.get_participant_enrollment(
                active_person
            )

        available_events = OneTimeEvent.get_available_events_by_participant(
            active_person
        )
        for event in available_events:
            event.active_person_can_enroll = event.can_person_enroll_as_participant(
                active_person
            )
            event.active_person_can_enroll_as_waiting = (
                event.can_person_enroll_as_waiting(active_person)
            )

        kwargs.setdefault("upcoming_events_participant", enrolled_events)
        kwargs.setdefault("available_events_participant", available_events)

    def _add_upcoming_events_organizer_kwargs(self, kwargs):
        """:meta private:"""

        active_person = self.request.active_person

        enrolled_events = OneTimeEvent.get_upcoming_by_organizer(active_person)
        available_events = OneTimeEvent.get_available_events_by_organizer(active_person)

        kwargs.setdefault("upcoming_events_organizer", enrolled_events)
        kwargs.setdefault("available_events_organizer", available_events)


class OneTimeEventAdminListView(EventAdminListMixin):
    """
    Displays the list of one-time events that the active user can manage.

    Filters using :class:`one_time_events.utils.OneTimeEventsFilter`.

    **Permissions**:

    Users that can manage at least one one-time event.

    **Query parameters:**

    *   ``category`` - filter
    *   ``date_from`` - filter
    *   ``date_to`` - filter
    *   ``state`` - filter
    """

    context_object_name = "events"
    template_name = "one_time_events/list_admin.html"

    def get(self, request, *args, **kwargs):
        """:meta private:"""

        self.filter_form = OneTimeEventsFilterForm(request.GET)
        return super().get(request, *args, **kwargs)

    def get_accessible_events(self):
        """:meta private:"""

        active_person = self.request.active_person
        active_user = get_active_user(active_person)

        events = OneTimeEvent.objects.all()
        visible_events_ids = [e.pk for e in events if e.can_user_manage(active_user)]

        return OneTimeEvent.objects.filter(pk__in=visible_events_ids)


class OneTimeEventCreateView(
    OneTimeEventCreatePermissionMixin,
    InsertRequestIntoModelFormKwargsMixin,
    EventGeneratesDatesMixin,
    EventCreateMixin,
):
    """
    Creates a one-time event.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the created event.

    **Permissions**:

    POST: Users that manage the event category sent in the request.
    GET: Users that manage at least one event category.

    **Request body parameters**:

    *   ``name``
    *   ``category``
    *   ``description``
    *   ``capacity``
    *   ``location``
    *   ``date_start``
    *   ``date_end``
    *   ``participants_enroll_state``
    *   ``dates``
    *   ``default_participation_fee``
    """

    form_class = OneTimeEventForm
    template_name = "one_time_events/create.html"


class OneTimeEventUpdateView(
    InsertRequestIntoModelFormKwargsMixin, EventGeneratesDatesMixin, EventUpdateMixin
):
    """
    Edits a one-time event.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the edited event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``pk`` - event ID

    **Request body parameters**:

    *   ``name``
    *   ``category``
    *   ``description``
    *   ``capacity``
    *   ``location``
    *   ``date_start``
    *   ``date_end``
    *   ``participants_enroll_state``
    *   ``dates``
    *   ``default_participation_fee``
    """

    form_class = OneTimeEventForm
    template_name = "one_time_events/edit.html"


class EditTrainingCategoryView(
    EventManagePermissionMixin, MessagesMixin, EventRestrictionMixin, generic.UpdateView
):
    """
    Edits the training category requirement of a one-time event.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the edited event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``pk`` - event ID

    **Request body parameters**:

    *   ``training_category`` - the new training category requirement
    """

    form_class = TrainingCategoryForm
    success_message = "Změna vyžadování skupiny uložena"
    template_name = "one_time_events/edit_training_category.html"


class OneTimeEventParticipantEnrollmentCreateUpdateMixin(
    EventManagePermissionMixin, InsertRequestIntoModelFormKwargsMixin
):
    """:meta private:"""

    event_id_key = "event_id"
    form_class = OneTimeEventParticipantEnrollmentForm
    model = OneTimeEventParticipantEnrollment


class OneTimeEventParticipantEnrollmentCreateView(
    OneTimeEventParticipantEnrollmentCreateUpdateMixin, ParticipantEnrollmentCreateMixin
):
    """
    Enrolls a person as a participant of a one-time event.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID

    **Request body parameters**:

    *   ``person``
    *   ``state``
    *   ``agreed_participation_fee``
    """

    template_name = "one_time_events/create_participant_enrollment.html"


class OneTimeEventParticipantEnrollmentUpdateView(
    OneTimeEventParticipantEnrollmentCreateUpdateMixin, ParticipantEnrollmentUpdateMixin
):
    """
    Edits a participant enrollment of a one-time event.

    Sends a notification email to the person if the enrollment was rejected.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID
    *   ``pk`` - enrollment ID

    **Request body parameters**:

    *   ``person``
    *   ``state``
    *   ``agreed_participation_fee``
    """

    template_name = "one_time_events/edit_participant_enrollment.html"


class OneTimeEventParticipantEnrollmentDeleteView(ParticipantEnrollmentDeleteMixin):
    """
    Removes a participant enrollment of a one-time event.

    Sends a notification email to the person about the change.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID
    *   ``pk`` - enrollment ID
    """

    template_name = "one_time_events/modals/delete_participant_enrollment.html"

    def form_valid(self, form):
        """:meta private:"""

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
    """
    Enrolls the active person as a participant of a one-time event.

    Sends a notification email to the person if they were enrolled as a substitute.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that can manage the event or interact with it.

    **Path parameters:**

    *   ``event_id`` - event ID
    """

    form_class = OneTimeEventEnrollMyselfParticipantForm
    model = OneTimeEventParticipantEnrollment
    success_message = "Přihlášení na událost proběhlo úspěšně"
    template_name = "one_time_events/modals/enroll_waiting.html"


class OrganizerForOccurrenceMixin(
    OccurrenceManagePermissionMixinID,
    RedirectToEventDetailOnSuccessMixin,
    MessagesMixin,
):
    """:meta private:"""

    pass


class AddOrganizerForOccurrenceView(
    OrganizerForOccurrenceMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertOccurrenceIntoContextData,
    generic.CreateView,
):
    """
    Assigns a person as an organizer of an occurrence of a one-time event.

    Sends a notification email to the person about the assignment.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that manage the occurrence.

    **Path parameters:**

    *   ``occurrence_id`` - occurrence ID

    **Request body parameters**:

    *   ``person``
    *   ``position_assignment``
    """

    form_class = OrganizerOccurrenceAssignmentForm
    model = OrganizerOccurrenceAssignment
    success_message = "Organizátor %(person)s přidán"
    template_name = "one_time_events/create_organizer_occurrence_assignment.html"


class EditOrganizerForOccurrenceView(OrganizerForOccurrenceMixin, generic.UpdateView):
    """
    Edits a person's assignment as an organizer of an occurrence of a one-time event.

    Sends a notification email to the person about the assignment.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that manage the occurrence.

    **Path parameters:**

    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - assignment ID

    **Request body parameters**:

    *   ``person``
    *   ``position_assignment``
    """

    context_object_name = "organizer_assignment"
    form_class = OrganizerOccurrenceAssignmentForm
    model = OrganizerOccurrenceAssignment
    success_message = "Organizátor %(person)s upraven"
    template_name = "one_time_events/edit_organizer_occurrence_assignment.html"

    def get_form_kwargs(self):
        """:meta private:"""

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
    """
    Removes a person's assignment as an organizer of an occurrence of a one-time event.

    Sends a notification email to the person about the change.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that manage the occurrence.

    **Path parameters:**

    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - assignment ID
    """

    context_object_name = "organizer_assignment"
    model = OrganizerOccurrenceAssignment
    template_name = "one_time_events/modals/delete_organizer_assignment.html"

    def get_success_message(self, cleaned_data):
        """:meta private:"""

        return f"Organizátor {self.object.person} odebrán"

    def form_valid(self, form):
        """:meta private:"""

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
    """:meta private:"""

    pass


class OrganizerSelectOccurrencesMixin:
    """:meta private:"""

    def get_context_data(self, **kwargs):
        kwargs.setdefault("checked_occurrences", self.get_form().checked_occurrences())
        return super().get_context_data(**kwargs)


class BulkDeleteOrganizerFromOneTimeEventView(
    BulkCreateDeleteOrganizerMixin,
    generic.FormView,
):
    """
    Deletes a person's assignment as an organizer from all occurrences
    of a one-time event.

    Sends a notification email to the person about the change.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID

    **Request body parameters**:

    *   ``person``
    """

    form_class = BulkDeleteOrganizerFromOneTimeEventForm
    success_message = "Organizátor %(person)s úspěšně odebrán ze všech dnů"
    template_name = "one_time_events/bulk_delete_organizer.html"

    def form_valid(self, form):
        """:meta private:"""

        person = form.cleaned_data["person"]
        event = self.event

        OrganizerOccurrenceAssignment.objects.filter(
            person=person,
            occurrence__event=event,
            occurrence__state=EventOrOccurrenceState.OPEN,
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
    """
    Assigns a person as an organizer to selected occurrences of a one-time event.

    Sends a notification email to the person about the assignment.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID

    **Request body parameters**:

    *   ``occurrences``
    *   ``person``
    *   ``position_assignment``
    """

    form_class = BulkAddOrganizerToOneTimeEventForm
    success_message = "Organizátor %(person)s přidán na vybrané dny"
    template_name = "one_time_events/bulk_add_organizer.html"


class OneTimeEventBulkApproveParticipantsView(
    InsertRequestIntoModelFormKwargsMixin, BulkApproveParticipantsMixin
):
    """
    Approves all participant enrollments of a one-time event.

    Sends a notification email to the person about the approval.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``pk`` - event ID

    **Request body parameters**:

    *   ``agreed_participation_fee``?
    """

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
    """
    Assigns the active person as an organizer of an occurrence of a one-time event.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that can be assigned the requested position in the occurrence.

    **Path parameters:**

    *   ``occurrence_id`` - occurrence ID
    *   ``position_assignment_id`` - position assignment ID
    """

    form_class = OneTimeEventEnrollMyselfOrganizerOccurrenceForm
    model = OrganizerOccurrenceAssignment
    success_message = "Přihlášení na organizátorskou pozici proběhlo úspěšně"


class OneTimeEventUnenrollMyselfOrganizerOccurrenceView(
    OccurrenceUnenrollOrganizerPermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    RedirectToEventDetailOnFailureMixin,
    generic.UpdateView,
):
    """
    Unassigns the active person as an organizer from an occurrence of a one-time event.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that can be unassigned the requested position in the occurrence.

    **Path parameters:**

    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - organizer assignment ID
    """

    context_object_name = "assignment"
    form_class = OneTimeEventUnenrollMyselfOrganizerOccurrenceForm
    model = OrganizerOccurrenceAssignment
    success_message = "Odhlášení z organizátorské pozice proběhlo úspěšně"
    template_name = "one_time_events/modals/unenroll_myself_organizer_occurrence.html"

    def form_valid(self, form):
        """:meta private:"""

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
    """
    Unassigns the active person as an organizer
    from all occurrences of a one-time event.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that can be unassigned from the assigned positions in the event.

    **Path parameters:**

    *   ``event_id`` - event ID
    """

    form_class = OneTimeEventUnenrollMyselfOrganizerForm
    success_message = "Odhlášení ze všech dnů události proběhlo úspěšně"
    template_name = "one_time_events/modals/unenroll_myself_organizer.html"

    def form_valid(self, form):
        """:meta private:"""

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
    """
    Assigns the active person as an organizer on a certain position
    to selected occurrences of a one-time event.

    **Success redirection view**: :class:`OneTimeEventDetailView` of the event.

    **Permissions**:

    Users that can be assigned the requested positions.

    **Path parameters:**

    *   ``event_id`` - event ID

    **Request body parameters**:

    *   ``occurrences``
    *   ``position_assignment``
    """

    form_class = OneTimeEventEnrollMyselfOrganizerForm
    success_message = "Přihlášení jako organizátor proběhlo úspěšně"
    template_name = "one_time_events/enroll_myself_organizer.html"


class OneTimeOccurrenceDetailView(OccurrenceDetailBaseView):
    """
    Detail of an occurrence of a one-time event.

    **Permissions**:

    Users that can manage the event occurrence or fill its attendance.

    **Path parameters:**

    *   ``event_id`` - event ID
    *   ``pk`` - occurrence ID
    """

    model = OneTimeEventOccurrence
    template_name = "one_time_events_occurrences/detail.html"


class OneTimeEventOccurrenceAttendanceCanBeFilledMixin:
    """:meta private:"""

    def dispatch(self, request, *args, **kwargs):
        """:meta private:"""

        occurrence = self.get_object()
        if today() < occurrence.date:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class OneTimeEventFillAttendanceInsertAssignmentsIntoContextData:
    """:meta private:"""

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
    """
    Fills the attendance of an occurrence of a one-time event.

    **Success redirection view**: :class:`OneTimeOccurrenceDetailView`
    of the occurrence.

    **Permissions**:

    Users that can fill the attendance of the occurrence.

    **Path parameters:**

    *   ``event_id`` - event ID
    *   ``pk`` - occurrence ID
    """

    form_class = OneTimeEventFillAttendanceForm
    model = OneTimeEventOccurrence
    occurrence_id_key = "pk"
    success_message = "Zapsání docházky proběhlo úspěšně"
    template_name = "one_time_events_occurrences/attendance.html"


class ApproveOccurrenceView(
    OccurrenceManagePermissionMixinPK,
    MessagesMixin,
    OneTimeEventFillAttendanceInsertAssignmentsIntoContextData,
    EventOccurrenceIdCheckMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    OccurrenceNotOpenedRestrictionMixin,
    InsertOccurrenceIntoContextData,
    InsertRequestIntoModelFormKwargsMixin,
    generic.UpdateView,
):
    """
    Approves the occurrence of a one-time event.

    **Success redirection view**: :class:`OneTimeOccurrenceDetailView`
    of the occurrence.

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters:**

    *   ``event_id`` - event ID
    *   ``pk`` - occurrence ID
    """

    form_class = ApproveOccurrenceForm
    model = OneTimeEventOccurrence
    occurrence_id_key = "pk"
    success_message = "Schválení proběhlo úspěšně"
    template_name = "one_time_events_occurrences/approve_occurrence.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("organizer_amounts", self.get_form().organizer_amounts())
        return super().get_context_data(**kwargs)


class ReopenOneTimeEventOccurrenceView(
    OccurrenceManagePermissionMixinPK,
    MessagesMixin,
    OccurrenceIsClosedRestrictionMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    EventOccurrenceIdCheckMixin,
    InsertOccurrenceIntoContextData,
    generic.UpdateView,
):
    """
    Reopens the occurrence of a one-time event.

    **Success redirection view**: :class:`OneTimeOccurrenceDetailView`
    of the occurrence.

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters:**

    *   ``event_id`` - event ID
    *   ``pk`` - occurrence ID
    """

    form_class = ReopenOneTimeEventOccurrenceForm
    model = OneTimeEventOccurrence
    occurrence_id_key = "pk"
    success_message = "Znovu otevření události a zrušení docházky proběhlo úspěšně"
    template_name = "one_time_events_occurrences/modals/reopen_occurrence.html"


class CancelOccurrenceApprovementView(
    OccurrenceManagePermissionMixinPK,
    MessagesMixin,
    OccurrenceIsApprovedRestrictionMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    EventOccurrenceIdCheckMixin,
    InsertOccurrenceIntoContextData,
    generic.UpdateView,
):
    """
    Cancels a one-time event occurrence approvement.

    **Success redirection view**: :class:`OneTimeOccurrenceDetailView`
    of the occurrence.

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters:**

    *   ``event_id`` - event ID
    *   ``pk`` - occurrence ID
    """

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
    """
    Displays an overview of open occurrences of a one-time event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID
    """

    template_name = "one_time_events/modals/open_occurrences_overview.html"


class OneTimeEventClosedOccurrencesOverviewView(
    EventManagePermissionMixin, InsertEventIntoContextData, generic.TemplateView
):
    """
    Displays an overview of closed occurrences of a one-time event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID
    """

    template_name = "one_time_events/modals/closed_occurrences_overview.html"


class OneTimeEventShowAttendanceView(
    EventManagePermissionMixin,
    MessagesMixin,
    InsertEventIntoContextData,
    generic.TemplateView,
):
    """
    Displays an overview of a one-time event's attendance.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID
    """

    template_name = "one_time_events/detail_components/show_attendance.html"


class OneTimeEventExportParticipantsView(
    EventManagePermissionMixin, InsertEventIntoSelfObjectMixin, generic.View
):
    """
    Exports the list of participants of a one-time event as a CSV file.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID
    """

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        """:meta private:"""

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
    """
    Exports the list of organizers of a one-time event as a CSV file.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID
    """

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        """:meta private:"""

        organizers_id = OrganizerOccurrenceAssignment.objects.filter(
            occurrence__event=self.event
        ).values_list("person_id")
        return export_queryset_csv(
            f"{self.event}_organizátoři", Person.objects.filter(id__in=organizers_id)
        )


class OneTimeEventExportOrganizersOccurrenceView(
    OccurrenceManagePermissionMixinPK,
    EventOccurrenceIdCheckMixin,
    InsertOccurrenceIntoSelfObjectMixin,
    generic.View,
):
    """
    Exports the list of organizers of an occurrence of a one-time event as a CSV file.

    **Permissions**:

    Users that manage the occurrence.

    **Path parameters:**

    *   ``event_id`` - event ID
    *   ``pk`` - occurrence ID
    """

    http_method_names = ["get"]
    occurrence_id_key = "pk"

    def get(self, request, *args, **kwargs):
        """:meta private:"""

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
    """
    Creates a duplicate of a one-time event.

    **Success redirection view**: :class:`OneTimeEventUpdateDuplicateView`
    of the duplicate event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``pk`` - event ID
    """

    form_class = OneTimeEventCreateDuplicateForm
    model = OneTimeEvent

    def form_valid(self, form):
        """:meta private:"""

        instance = form.instance
        new_event = instance.duplicate()

        for position_assignment in instance.eventpositionassignment_set.all():
            position_assignment.duplicate(new_event)

        for occurrence in instance.eventoccurrence_set.all():
            occurrence.duplicate(new_event)

        self.event_id = new_event.id
        return super().form_valid(form)

    def get_success_url(self):
        """:meta private:"""

        return reverse("one_time_events:edit-duplicate", args=[self.event_id])


class OneTimeEventUpdateDuplicateView(
    InsertRequestIntoModelFormKwargsMixin,
    EventGeneratesDatesMixin,
    EventUpdateMixin,
    RedirectToEventDetailOnSuccessMixin,
):
    """
    Edits a created duplicate one-time event.

    **Success redirection view**: :class:`OneTimeEventDetailView`
    of the duplicated event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``pk`` - event ID

    **Request body parameters**:

    *   ``name``
    *   ``category``
    *   ``description``
    *   ``capacity``
    *   ``location``
    *   ``date_start``
    *   ``date_end``
    *   ``participants_enroll_state``
    *   ``dates``
    *   ``default_participation_fee``
    """

    form_class = OneTimeEventForm
    template_name = "one_time_events/edit_duplicate.html"
