from datetime import timedelta

from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from events.models import ParticipantEnrollment
from events.permissions import (
    EventManagePermissionMixin,
    OccurrenceEnrollOrganizerPermissionMixin,
    OccurrenceManagePermissionMixinID,
    OccurrenceManagePermissionMixinPK,
    OccurrenceUnenrollOrganizerPermissionMixin,
)
from events.views import (
    BulkApproveParticipantsMixin,
    EnrollMyselfParticipantMixin,
    EventAdminListMixin,
    EventCreateMixin,
    EventDetailMixin,
    EventGeneratesDatesMixin,
    EventOccurrenceIdCheckMixin,
    EventUpdateMixin,
    InsertEventIntoContextData,
    InsertEventIntoSelfObjectMixin,
    InsertOccurrenceIntoContextData,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertOccurrenceIntoSelfObjectMixin,
    InsertPositionAssignmentIntoModelFormKwargs,
    OccurrenceDetailBaseView,
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
from one_time_events.permissions import OccurrenceFillAttendancePermissionMixin
from persons.models import Person, get_active_user
from trainings.permissions import (
    OccurrenceEnrollMyselfParticipantPermissionMixin,
    OccurrenceExcuseMyselfOrganizerPermissionMixin,
    OccurrenceExcuseMyselfParticipantPermissionMixin,
    OccurrenceUnenrollMyselfParticipantPermissionMixin,
    TrainingCreatePermissionMixin,
)
from users.permissions import LoginRequiredMixin
from vzs.mixins import (
    InsertActivePersonIntoModelFormKwargsMixin,
    InsertRequestIntoModelFormKwargsMixin,
    MessagesMixin,
)
from vzs.settings import PARTICIPANT_ENROLL_DEADLINE_DAYS
from vzs.utils import date_pretty, export_queryset_csv, now, send_notification_email

from .forms import (
    CancelCoachExcuseForm,
    CancelParticipantExcuseForm,
    CoachAssignmentDeleteForm,
    CoachExcuseForm,
    CoachOccurrenceAssignmentForm,
    ExcuseMyselfCoachForm,
    ExcuseMyselfParticipantForm,
    ParticipantExcuseForm,
    ReopenTrainingOccurrenceForm,
    TrainingBulkApproveParticipantsForm,
    TrainingEnrollMyselfOrganizerOccurrenceForm,
    TrainingEnrollMyselfParticipantForm,
    TrainingEnrollMyselfParticipantOccurrenceForm,
    TrainingFillAttendanceForm,
    TrainingForm,
    TrainingParticipantAttendanceForm,
    TrainingReplaceableForm,
    TrainingsFilterForm,
    TrainingUnenrollMyselfOrganizerFromOccurrenceForm,
    TrainingUnenrollMyselfParticipantFromOccurrenceForm,
)
from .mixins import (
    CoachAssignmentCreateUpdateMixin,
    CoachAssignmentMixin,
    InsertAvailableCategoriesIntoFormsKwargsMixin,
    TrainingOccurrenceAttendanceCanBeFilledMixin,
    TrainingParticipantEnrollmentCreateUpdateMixin,
    TrainingWeekdaysSelectionMixin,
)
from .models import (
    CoachOccurrenceAssignment,
    CoachPositionAssignment,
    Training,
    TrainingAttendance,
    TrainingOccurrence,
    TrainingParticipantAttendance,
    TrainingParticipantEnrollment,
    TrainingReplaceabilityForParticipants,
)


class TrainingDetailView(EventDetailMixin):
    """
    Displays an admin detail of a training.

    **Permissions**:

    Users that can manage the training or interact with it.

    **Path parameters**:

    *   ``pk`` - training ID
    """

    def get_context_data(self, **kwargs):
        """
        *   ``trainings_for_replacement`` - trainings that can be added
            as a possible replacement for this training
        *   ``selected_replaceable_trainings`` - trainings that
            can replace this training
        *   ``active_person_participant_enrollment`` - participant enrollment
            of the active person
        *   ``enrollment_states`` - possible states of participant enrollment
        *   ``upcoming_occurrences`` - upcoming occurrences of this training
        *   ``past_occurrences`` - past occurrences of this training
        *   ``upcoming_one_time_occurrences`` - upcoming occurrences of this training
            where the active person is one time participant
        *   ``participants_by_weekdays`` - participants of this training
            grouped by weekdays
        *   ``occurrences`` - occurrences of this training
        """

        active_person = self.request.active_person
        trainings_for_replacement_to_choose = (
            Training.objects.filter(
                category=self.object.category,
            )
            .exclude(pk=self.object.pk)
            .exclude(replaceable_training_2__training_1=self.object)
        )

        upcoming_occurrences = self.object.sorted_occurrences_list().filter(
            datetime_start__gte=now()
        )[:10]
        for occurrence in upcoming_occurrences:
            occurrence.can_excuse = occurrence.can_participant_excuse(active_person)
            participant_attendance = occurrence.get_participant_attendance(
                active_person
            )
            occurrence.excused = (
                participant_attendance
                and participant_attendance.state == TrainingAttendance.EXCUSED
            )

        past_occurrences = self.object.sorted_occurrences_list().filter(
            datetime_start__lte=now()
        )[:20]
        for occurrence in past_occurrences:
            if occurrence.is_closed and occurrence.get_participant_attendance(
                active_person
            ):
                occurrence.participant_attendance = (
                    occurrence.get_participant_attendance(active_person).state
                )
            else:
                occurrence.participant_attendance = "not_closed"

        selected_replaceable_trainings = (
            TrainingReplaceabilityForParticipants.objects.filter(training_1=self.object)
        )

        upcoming_one_time_occurrences = []
        if not self.object.enrolled_participants.filter(pk=active_person.pk).exists():
            upcoming_one_time_occurrences = (
                self.object.sorted_occurrences_list()
                .filter(
                    datetime_start__gte=now(),
                    trainingparticipantattendance__person=active_person,
                    trainingparticipantattendance__state=TrainingAttendance.PRESENT,
                )
                .all()
            )

        kwargs.setdefault(
            "trainings_for_replacement", trainings_for_replacement_to_choose
        )
        kwargs.setdefault(
            "selected_replaceable_trainings", selected_replaceable_trainings
        )
        kwargs.setdefault(
            "active_person_participant_enrollment",
            self.object.get_participant_enrollment(active_person),
        )
        kwargs.setdefault("enrollment_states", ParticipantEnrollment.State)
        kwargs.setdefault("upcoming_occurrences", upcoming_occurrences)
        kwargs.setdefault("past_occurrences", past_occurrences)
        kwargs.setdefault(
            "upcoming_one_time_occurrences", upcoming_one_time_occurrences
        )

        self._add_coaches_detail_kwargs(kwargs)

        return super().get_context_data(**kwargs)

    def get_template_names(self):
        """:meta private:"""

        active_person = self.request.active_person
        active_user = get_active_user(active_person)
        if self.object.can_user_manage(active_user):
            return "trainings/detail_admin.html"
        elif self.object.is_organizer(active_person):
            return "trainings/detail_coach.html"
        else:
            return "trainings/detail_participant.html"

    def _add_coaches_detail_kwargs(self, kwargs):
        """:meta private:"""

        occurrences = self.object.sorted_occurrences_list()

        nearest_occurrence_found = False
        for occurrence in occurrences:
            occurrence.is_excused = occurrence.is_coach_excused(
                self.request.active_person
            )
            if not nearest_occurrence_found and occurrence.datetime_start >= now():
                occurrence.nearest_occurrence = True
                nearest_occurrence_found = True

        participants_by_weekdays = {}
        for weekday in self.object.weekdays_list():
            participants_by_weekdays[
                weekday
            ] = self.object.approved_enrollments_by_weekday(weekday).order_by(
                "person__last_name"
            )

        kwargs.setdefault("participants_by_weekdays", participants_by_weekdays)
        kwargs.setdefault("occurrences", occurrences)


class TrainingListView(LoginRequiredMixin, generic.ListView):
    """
    Displays a list of all trainings related to the active person.

    **Permissions**:

    Logged in users.
    """

    template_name = "trainings/index.html"

    def get_context_data(self, **kwargs):
        """
        *   ``coach_regular_trainings`` - trainings where the active person
            is a coach
        *   ``coach_upcoming_occurrences`` - upcoming occurrences where
            the active person is a coach
        *   ``participant_enrolled_trainings`` - trainings where the active person
            is enrolled as a participant
        *   ``participant_available_trainings`` - trainings where the active person
            can enroll as a participant
        *   ``participant_upcoming_occurrences`` - upcoming occurrences where
            the active person is a participant
        """

        active_person = self.request.active_person

        self._add_participant_kwargs(kwargs, active_person)
        self._add_coaches_kwargs(kwargs, active_person)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """:meta private:"""

        return []

    def _add_coaches_kwargs(self, kwargs, active_person):
        """:meta private:"""

        regular_trainings = Training.get_unfinished_trainings_by_coach(active_person)
        upcoming_occurrences = TrainingOccurrence.get_upcoming_by_coach(
            active_person, False
        ).all()

        for occurrence in upcoming_occurrences:
            occurrence.excused = occurrence.is_coach_excused(active_person)

        kwargs.setdefault("coach_regular_trainings", regular_trainings)
        kwargs.setdefault("coach_upcoming_occurrences", upcoming_occurrences)

    def _add_participant_kwargs(self, kwargs, active_person):
        """:meta private:"""

        available_trainings = Training.get_available_trainings_by_participant(
            active_person
        )
        enrolled_trainings = Training.get_unfinished_trainings_by_participant(
            active_person
        )
        upcoming_occurrences = TrainingOccurrence.get_upcoming_by_participant(
            active_person, False
        ).all()

        for occurrence in upcoming_occurrences:
            participant_attendance = occurrence.get_participant_attendance(
                active_person
            )
            occurrence.excused = (
                participant_attendance and participant_attendance.is_excused
            )
            occurrence.is_one_time_presence = (
                participant_attendance.is_one_time_presence
            )

        kwargs.setdefault("participant_enrolled_trainings", enrolled_trainings)
        kwargs.setdefault("participant_available_trainings", available_trainings)
        kwargs.setdefault("participant_upcoming_occurrences", upcoming_occurrences)

        self._add_trainings_replacing_kwargs(kwargs, active_person, enrolled_trainings)

    def _add_trainings_replacing_kwargs(
        self, kwargs, active_person, enrolled_trainings
    ):
        """:meta private:"""

        count_of_trainings_to_replace = (
            TrainingParticipantAttendance.count_of_trainings_to_replace(active_person)
        )

        if count_of_trainings_to_replace <= 0:
            return

        replaceable_trainings = []

        for enrolled_training in enrolled_trainings:
            replaceable_trainings += enrolled_training.replaces_training_list()

        date_start = now() + timedelta(days=PARTICIPANT_ENROLL_DEADLINE_DAYS)
        replaceable_occurrences = (
            TrainingOccurrence.objects.filter(
                datetime_start__gte=date_start, event__in=replaceable_trainings
            )
            .exclude(participants=active_person)
            .order_by("datetime_start")
        )

        available_replaceable_occurrences = [
            o for o in replaceable_occurrences if o.has_free_participant_spot()
        ][:10]

        kwargs.setdefault(
            "participant_count_of_trainings_to_replace", count_of_trainings_to_replace
        )
        kwargs.setdefault(
            "participant_replaceable_occurrences", available_replaceable_occurrences
        )


class TrainingAdminListView(TrainingCreatePermissionMixin, EventAdminListMixin):
    """
    Displays an admin list of all trainings.

    Uses :class:`TrainingsFilterForm` to filter trainings.

    Users only see trainings they can manage.

    **Permissions**:

    Users that can manage at least one training category.

    **Query parameters**:

    *   ``category``
    *   ``year_start``
    *   ``main_coach``
    *   ``only_opened``
    """

    template_name = "trainings/list_admin.html"
    context_object_name = "trainings"

    def get(self, request, *args, **kwargs):
        """:meta private:"""

        self.filter_form = TrainingsFilterForm(request.GET)
        return super().get(request, *args, **kwargs)

    def get_accessible_events(self):
        """:meta private:"""

        active_person = self.request.active_person
        active_user = get_active_user(active_person)

        trainings = Training.objects.all()
        visible_trainings_ids = [
            t.pk for t in trainings if t.can_user_manage(active_user)
        ]

        return Training.objects.filter(pk__in=visible_trainings_ids)


class TrainingCreateView(
    TrainingCreatePermissionMixin,
    InsertAvailableCategoriesIntoFormsKwargsMixin,
    EventGeneratesDatesMixin,
    EventCreateMixin,
):
    """
    Creates a training.

    **Success redirection view**: :class:`TrainingDetailView` of the created training.

    **Permissions**:

    POST: Users that manage the training category sent in the request.
    GET: Users that manage at least one training category.

    **Request body parameters**:

    *   ``category``
    *   ``po_from``
    *   ``po_to``
    *   ``ut_from``
    *   ``ut_to``
    *   ``st_from``
    *   ``st_to``
    *   ``ct_from``
    *   ``ct_to``
    *   ``pa_from``
    *   ``pa_to``
    *   ``so_from``
    *   ``so_to``
    *   ``ne_from``
    *   ``ne_t``
    *   ``name``
    *   ``category``
    *   ``description``
    *   ``capacity``
    *   ``location``
    *   ``date_start``
    *   ``date_end``
    *   ``participants_enroll_state``
    """

    template_name = "trainings/create.html"
    form_class = TrainingForm


class TrainingUpdateView(
    InsertAvailableCategoriesIntoFormsKwargsMixin,
    EventGeneratesDatesMixin,
    EventUpdateMixin,
):
    """
    Edits a training.

    **Success redirection view**: :class:`TrainingDetailView` of the edited training

    **Permissions**:

    Users that manage the training.

    **Path parameters:**

    *   ``pk`` - training ID

    **Request body parameters**:

    *   ``category``
    *   ``po_from``
    *   ``po_to``
    *   ``ut_from``
    *   ``ut_to``
    *   ``st_from``
    *   ``st_to``
    *   ``ct_from``
    *   ``ct_to``
    *   ``pa_from``
    *   ``pa_to``
    *   ``so_from``
    *   ``so_to``
    *   ``ne_from``
    *   ``ne_t``
    *   ``name``
    *   ``category``
    *   ``description``
    *   ``capacity``
    *   ``location``
    *   ``date_start``
    *   ``date_end``
    *   ``participants_enroll_state``
    """

    template_name = "trainings/edit.html"
    form_class = TrainingForm


class TrainingAddReplaceableTrainingView(
    EventManagePermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    RedirectToEventDetailOnFailureMixin,
    generic.CreateView,
):
    """
    Adds a training as a possible replacement for a training. Both directions
    of the relation are added.

    **Success redirection view**: :class:`TrainingDetailView` of the training

    **Permissions**:

    Users that manage the training.

    **Path parameters:**

    *   ``event_id`` - training ID

    **Request body parameters**:

    *   ``training_2`` - ID of the training to add as a possible replacement
    """

    form_class = TrainingReplaceableForm
    success_message = _("Tréninky pro náhrady byl přidán.")
    model = TrainingReplaceabilityForParticipants
    event_id_key = "event_id"

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs["training_1"] = get_object_or_404(Training, pk=self.kwargs["event_id"])
        return kwargs


class TrainingRemoveReplaceableTrainingView(EventManagePermissionMixin, generic.View):
    """
    Removes a training as a possible replacement for a training.
    Removes both directions of the relation.

    **Success redirection view**: :class:`TrainingDetailView` of the training

    **Permissions**:

    Users that manage the training.

    **Path parameters:**

    *   ``event_id`` - training ID

    **Request body parameters**:

    *   ``training_2`` - ID of the training to remove as a possible replacement
    """

    http_method_names = ["post"]
    event_id_key = "event_id"

    def post(self, request, event_id, *args, **kwargs):
        """:meta private:"""

        training_1 = event_id
        training_2 = request.POST.get("training_2")

        removed_items_count, _ = TrainingReplaceabilityForParticipants.objects.filter(
            Q(training_1=training_1, training_2=training_2)
            | Q(training_2=training_1, training_1=training_2)
        ).delete()

        if 1 <= removed_items_count <= 2:
            messages.success(request, "Tréninky pro náhrady byly odebrány.")
        else:
            messages.error(request, "Nebyly nalezeny tréninky k odebrání.")

        return redirect(reverse("trainings:detail", args=[event_id]))


class TrainingParticipantEnrollmentCreateView(
    TrainingParticipantEnrollmentCreateUpdateMixin, ParticipantEnrollmentCreateMixin
):
    """
    Enrolls a person as a participant of a training.

    **Success redirection view**: :class:`TrainingDetailView` of the training

    **Permissions**:

    Users that can manage the training.

    **Path parameters:**

    *   ``event_id`` - training ID

    **Request body parameters**:

    *   ``person``
    *   ``state``
    *   ``weekdays``
    """

    template_name = "trainings/create_participant_enrollment.html"


class TrainingParticipantEnrollmentUpdateView(
    TrainingParticipantEnrollmentCreateUpdateMixin, ParticipantEnrollmentUpdateMixin
):
    """
    Edits a person's enrollment for a training.

    **Success redirection view**: :class:`TrainingDetailView` of the training

    **Permissions**:

    Users that can manage the training.

    **Path parameters:**

    *   ``event_id`` - training ID
    *   ``pk`` - enrollment ID

    **Request body parameters**:

    *   ``person``
    *   ``state``
    *   ``weekdays``
    """

    template_name = "trainings/edit_participant_enrollment.html"


class TrainingParticipantEnrollmentDeleteView(ParticipantEnrollmentDeleteMixin):
    """
    Unenrolls a person from a training.

    Sends a notification email to the person.

    **Success redirection view**: :class:`TrainingDetailView` of the training

    **Permissions**:

    Users that can manage the training.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``pk`` - enrollment ID
    """

    template_name = "trainings/modals/delete_participant_enrollment.html"

    def form_valid(self, form):
        """:meta private:"""

        enrollment = self.object
        if enrollment.state == ParticipantEnrollment.State.REJECTED:
            send_notification_email(
                _("Zrušení odmítnutí účasti"),
                _(
                    f"Na trénink {enrollment.event} vám bylo umožněno znovu se přihlásit"
                ),
                [enrollment.person],
            )
        else:
            send_notification_email(
                _("Odstranění přihlášky"),
                _(
                    f"Vaše přihláška na trénink {enrollment.event} byla smazána administrátorem"
                ),
                [enrollment.person],
            )
        return super().form_valid(form)


class TrainingEnrollMyselfParticipantView(
    TrainingWeekdaysSelectionMixin, EnrollMyselfParticipantMixin
):
    """
    Enrolls the active person as a participant of a training.

    **Success redirection view**: :class:`TrainingDetailView` of the training

    **Permissions**:

    Users that can interact with the training.

    **Path parameters**:

    *   ``event_id`` - training ID

    **Request body parameters**:

    *   ``weekdays``
    """

    model = TrainingParticipantEnrollment
    form_class = TrainingEnrollMyselfParticipantForm
    template_name = "trainings/enroll_myself_participant.html"
    success_message = "Přihlášení na trénink proběhlo úspěšně"


class CoachAssignmentCreateView(CoachAssignmentCreateUpdateMixin, generic.CreateView):
    """
    Assigns a person as a coach of a training on a certain position.

    **Success redirection view**: :class:`TrainingDetailView` of the training

    **Permissions**:

    Users that can manage the training.

    **Path parameters**:

    *   ``event_id`` - training ID

    **Request body parameters**:

    *   ``person``
    *   ``position_assignment``
    """

    template_name = "trainings/create_coach_assignment.html"
    success_message = "Trenér %(person)s přidán"


class CoachAssignmentUpdateView(CoachAssignmentCreateUpdateMixin, generic.UpdateView):
    """
    Edits a coach assignment.

    **Success redirection view**: :class:`TrainingDetailView` of the training

    **Permissions**:

    Users that can manage the training.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``pk`` - assignment ID

    **Request body parameters**:

    *   ``person``
    *   ``position_assignment``
    """

    template_name = "trainings/edit_coach_assignment.html"
    success_message = "Trenér %(person)s upraven"

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs["person"] = self.object.person
        return kwargs


class CoachAssignmentDeleteView(CoachAssignmentMixin, generic.UpdateView):
    """
    Unassigns a person from a training as a coach.

    Sends a notification email to the person.

    **Success redirection view**: :class:`TrainingDetailView` of the training

    **Permissions**:

    Users that can manage the training.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``pk`` - assignment ID
    """

    success_message = "Odhlášení trenéra proběhlo úspěšně"
    template_name = "trainings/modals/delete_coach_assignment.html"
    form_class = CoachAssignmentDeleteForm
    event_id_key = "event_id"


class TrainingBulkApproveParticipantsView(BulkApproveParticipantsMixin):
    """
    Approved all participant enrollments of a training.

    **Success redirection view**: :class:`TrainingDetailView` of the training

    **Permissions**:

    Users that can manage the training.

    **Path parameters**:

    *   ``pk`` - training ID
    """

    form_class = TrainingBulkApproveParticipantsForm


class TrainingOccurrenceDetailView(OccurrenceDetailBaseView):
    """
    Displays a detail of a training occurrence.

    **Permissions**:

    Users that can manage the event occurrence or fill its attendance.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``pk`` - occurrence ID
    """

    model = TrainingOccurrence
    template_name = "trainings_occurrences/detail.html"

    def get_context_data(self, **kwargs):
        """
        *   ``active_person_can_coach_excuse`` - whether the active person
            can excuse themselves as a coach
        *   ``active_person_can_participant_excuse`` - whether the active person
            can excuse themselves as a participant
        *   ``active_person_can_participant_unenroll`` - whether the active person
            can unenroll themselves as a participant
        *   ``active_person_can_participant_enroll`` - whether the active person
            can enroll themselves as a participant
        """

        active_person = self.request.active_person
        kwargs.setdefault(
            "active_person_can_coach_excuse",
            self.object.can_coach_excuse(active_person),
        )
        kwargs.setdefault(
            "active_person_can_participant_excuse",
            self.object.can_participant_excuse(active_person),
        )
        kwargs.setdefault(
            "active_person_can_participant_unenroll",
            self.object.can_participant_unenroll(active_person),
        )
        kwargs.setdefault(
            "active_person_can_participant_enroll",
            self.object.can_participant_enroll(active_person),
        )
        return super().get_context_data(**kwargs)


class CoachOccurrenceBaseView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    OccurrenceOpenRestrictionMixin,
    generic.FormView,
):
    """:meta private:"""

    model = CoachOccurrenceAssignment
    context_object_name = "assignment"


class CancelCoachExcuseView(
    OccurrenceManagePermissionMixinID,
    CoachOccurrenceBaseView,
    generic.UpdateView,
):
    """
    Cancels a coach excuse.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - coach assignment ID
    """

    form_class = CancelCoachExcuseForm
    template_name = "trainings_occurrences/modals/cancel_coach_excuse.html"
    success_message = "Zrušení omluvenky trenéra proběhlo úspěšně"


class ExcuseMyselfCoachView(
    OccurrenceExcuseMyselfOrganizerPermissionMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    CoachOccurrenceBaseView,
    generic.UpdateView,
):
    """
    Excuses the active person as a coach from a training occurrence.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can excuse themselves as a coach of the training occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    """

    form_class = ExcuseMyselfCoachForm
    template_name = "trainings_occurrences/modals/excuse_myself_coach.html"
    success_message = "Vaše trenérská neúčast byla úspěšně nahlášena"

    def get_object(self, queryset=None):
        """:meta private:"""

        active_person = self.request.active_person
        if active_person is None:
            raise Http404("Tato stránka není dostupná")

        occurrence = get_object_or_404(
            TrainingOccurrence, pk=self.kwargs["occurrence_id"]
        )
        return CoachOccurrenceAssignment.objects.get(
            person=active_person, occurrence=occurrence
        )


class CoachExcuseView(
    OccurrenceManagePermissionMixinID,
    CoachOccurrenceBaseView,
    generic.UpdateView,
):
    """
    Excuses a coach from a training occurrence.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - coach assignment ID
    """

    form_class = CoachExcuseForm
    template_name = "trainings_occurrences/modals/coach_excuse.html"
    success_message = "Omluvení trenéra proběhlo úspěšně"


class EnrollMyselfOrganizerForOccurrenceView(
    OccurrenceEnrollOrganizerPermissionMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertPositionAssignmentIntoModelFormKwargs,
    CoachOccurrenceBaseView,
    generic.CreateView,
):
    """
    Adds the active person as a one-time coach on a certain position
    of a training occurrence.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can enroll on the position in the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    *   ``position_assignment_id`` - position assignment ID
    """

    form_class = TrainingEnrollMyselfOrganizerOccurrenceForm
    success_message = "Přihlášení jako jednorázový trenér proběhlo úspěšně"
    template_name = "trainings_occurrences/detail.html"


class OneTimeCoachDeleteView(
    OccurrenceManagePermissionMixinID,
    CoachOccurrenceBaseView,
    generic.DeleteView,
):
    """
    Unassigns a person from a training occurrence as a one-time coach.

    Sends a notification email to the person.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - coach assignment ID
    """

    template_name = "trainings_occurrences/modals/delete_one_time_coach.html"

    def get_success_message(self, cleaned_data):
        """:meta private:"""

        return (
            f"Osoba {self.object.person} byla úspěšně odebrána jako jednorázový trenér"
        )

    def form_valid(self, form):
        """:meta private:"""

        assignment = self.object
        send_notification_email(
            _("Zrušení jednorázové trenérské účasti"),
            _(
                f"Vaše jednorázová trenérská účast na pozici {assignment.position_assignment.position} dne {date_pretty(assignment.occurrence.datetime_start)} tréninku {assignment.occurrence.event} byla zrušena administrátorem"
            ),
            [assignment.person],
        )
        return super().form_valid(form)


class UnenrollMyselfOrganizerFromOccurrenceView(
    OccurrenceUnenrollOrganizerPermissionMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    CoachOccurrenceBaseView,
    generic.UpdateView,
):
    """
    Unenrolls the active person from a training occurrence as a one-time coach.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can unenroll from the position in the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - coach assignment ID
    """

    form_class = TrainingUnenrollMyselfOrganizerFromOccurrenceForm
    template_name = (
        "trainings_occurrences/modals/unenroll_myself_organizer_occurrence.html"
    )

    def get_success_message(self, cleaned_data):
        """:meta private:"""

        return f"Odhlášení z jednorázové trenérské pozice proběhlo úspěšně"


class AddOneTimeCoachView(
    OccurrenceManagePermissionMixinID,
    InsertOccurrenceIntoModelFormKwargsMixin,
    CoachOccurrenceBaseView,
    generic.CreateView,
):
    """
    Assigns a person as a one-time coach of a training occurrence on a certain position.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID

    **Request body parameters**:

    *   ``person``
    *   ``position_assignment``
    """

    form_class = CoachOccurrenceAssignmentForm
    template_name = "trainings_occurrences/create_coach_occurrence_assignment.html"
    success_message = "Jednorázový trenér %(person)s přidán"


class EditOneTimeCoachView(
    OccurrenceManagePermissionMixinID,
    MessagesMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    OccurrenceOpenRestrictionMixin,
    generic.UpdateView,
):
    """
    Edits a one-time coach assignment.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - coach assignment ID

    **Request body parameters**:

    *   ``person``
    *   ``position_assignment``
    """

    model = CoachOccurrenceAssignment
    form_class = CoachOccurrenceAssignmentForm
    context_object_name = "assignment"
    template_name = "trainings_occurrences/edit_coach_occurrence_assignment.html"
    success_message = "Přihláska jednorázového trenéra %(person)s upravena"

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs["occurrence"] = self.object.occurrence
        kwargs["person"] = self.object.person
        return kwargs

    def get_context_data(self, **kwargs):
        """
        *   ``occurrence`` - occurrence of the assignment
        *   ``event`` - training associated with the occurrence
        """

        kwargs.setdefault("occurrence", self.object.occurrence)
        kwargs.setdefault("event", self.object.occurrence.event)
        return super().get_context_data(**kwargs)


class ParticipantOccurrenceBaseView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    OccurrenceOpenRestrictionMixin,
    generic.FormView,
):
    """:meta private:"""

    model = TrainingParticipantAttendance
    context_object_name = "participant_attendance"


class ExcuseParticipantView(
    OccurrenceManagePermissionMixinID,
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    """
    Excuces a participant from a training occurrence.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - participant attendance ID
    """

    form_class = ParticipantExcuseForm
    template_name = "trainings_occurrences/modals/participant_excuse.html"
    success_message = "Omluvení účastníka proběhlo úspěšně"


class CancelParticipantExcuseView(
    OccurrenceManagePermissionMixinID,
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    """
    Cancels a training occurrence participant excuse.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - participant attendance ID
    """

    form_class = CancelParticipantExcuseForm
    template_name = "trainings_occurrences/modals/cancel_participant_excuse.html"
    success_message = "Zrušení omluvenky účastníka proběhlo úspěšně"


class ExcuseMyselfParticipantView(
    OccurrenceExcuseMyselfParticipantPermissionMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    """
    Excuses the active person as a participant from a training occurrence.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can excuse themselves as a participant of the training occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    """

    form_class = ExcuseMyselfParticipantForm
    template_name = "trainings_occurrences/modals/excuse_myself_participant.html"
    success_message = "Vaše neúčast jako účastník byla úspěšně nahlášena"

    def get_object(self, queryset=None):
        """:meta private:"""

        active_person = self.request.active_person
        if active_person is None:
            raise Http404("Tato stránka není dostupná")

        occurrence = get_object_or_404(
            TrainingOccurrence, pk=self.kwargs["occurrence_id"]
        )
        return TrainingParticipantAttendance.objects.get(
            person=active_person, occurrence=occurrence
        )


class UnenrollMyselfParticipantFromOccurrenceView(
    OccurrenceUnenrollMyselfParticipantPermissionMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    """
    Unenrolls the active person from a training occurrence as a one-time participant.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can unenroll themselves as a participant of the training occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - participant attendance ID
    """

    form_class = TrainingUnenrollMyselfParticipantFromOccurrenceForm
    template_name = (
        "trainings_occurrences/modals/unenroll_myself_participant_occurrence.html"
    )
    success_message = "Odhlášení jako jednorázový účastník proběhlo úspěšně"


class AddOneTimeParticipantView(
    OccurrenceManagePermissionMixinID,
    InsertOccurrenceIntoModelFormKwargsMixin,
    ParticipantOccurrenceBaseView,
    generic.CreateView,
):
    """
    Enrolls a person as a one-time participant of a training occurrence.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID

    **Request body parameters**:

    *   ``person``
    """

    form_class = TrainingParticipantAttendanceForm
    template_name = "trainings_occurrences/create_one_time_participant.html"
    success_message = "Jednorázový účastník %(person)s přidán"


class OneTimeParticipantDeleteView(
    OccurrenceManagePermissionMixinID,
    ParticipantOccurrenceBaseView,
    generic.DeleteView,
):
    """
    Unenrolls a person from a training occurrence as a one-time participant.

    Sends a notification email to the person.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    *   ``pk`` - participant attendance ID
    """

    template_name = "trainings_occurrences/modals/delete_one_time_participant.html"

    def get_success_message(self, cleaned_data):
        """:meta private:"""

        return f"Osoba {self.object.person} byla úspěšně odebrána jako účastník"

    def form_valid(self, form):
        """:meta private:"""

        attendance = self.object
        send_notification_email(
            _("Zrušení jednorázové účasti účastníka"),
            _(
                f"Vaše jednorázová účast dne {date_pretty(attendance.occurrence.datetime_start)} tréninku {attendance.occurrence.event} byla zrušena administrátorem"
            ),
            [attendance.person],
        )
        return super().form_valid(form)


class EnrollMyselfParticipantFromOccurrenceView(
    OccurrenceEnrollMyselfParticipantPermissionMixin,
    MessagesMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    EventOccurrenceIdCheckMixin,
    OccurrenceOpenRestrictionMixin,
    generic.CreateView,
):
    """
    Enrolls the active person as a one-time participant of a training occurrence.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can enroll themselves as a participant of the training occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``occurrence_id`` - occurrence ID
    """

    form_class = TrainingEnrollMyselfParticipantOccurrenceForm
    success_message = "Přihlášení jako jednorázový účastník proběhlo úspěšně"
    template_name = "trainings_occurrences/detail.html"


class TrainingFillAttendanceView(
    OccurrenceFillAttendancePermissionMixin,
    MessagesMixin,
    TrainingOccurrenceAttendanceCanBeFilledMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    InsertOccurrenceIntoContextData,
    InsertRequestIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
    generic.UpdateView,
):
    """
    Fills the attendance of a training occurrence.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can fill the attendance of the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``pk`` - occurrence ID

    **Request body parameters**:

    *   ``coaches``
    *   ``participants``
    """

    form_class = TrainingFillAttendanceForm
    model = TrainingOccurrence
    occurrence_id_key = "pk"
    success_message = "Zapsání docházky proběhlo úspěšně"
    template_name = "trainings_occurrences/attendance.html"

    def get_context_data(self, **kwargs):
        """
        *   ``participant_assignments`` - participant assignments of the occurrence
        *   ``coach_assignments`` - coach assignments of the occurrence
        """

        kwargs.setdefault(
            "participant_assignments", self.get_form().checked_participant_assignments()
        )
        kwargs.setdefault(
            "coach_assignments", self.get_form().checked_coach_assignments()
        )
        return super().get_context_data(**kwargs)


class ReopenTrainingOccurrenceView(
    OccurrenceManagePermissionMixinPK,
    MessagesMixin,
    OccurrenceNotOpenedRestrictionMixin,
    RedirectToOccurrenceFallbackEventDetailOnSuccessMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    EventOccurrenceIdCheckMixin,
    InsertOccurrenceIntoContextData,
    generic.UpdateView,
):
    """
    Reopens a training occurrence.

    **Success redirection view**: :class:`TrainingOccurrenceDetailView`
    of the occurrence

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``pk`` - occurrence ID
    """

    form_class = ReopenTrainingOccurrenceForm
    model = TrainingOccurrence
    occurrence_id_key = "pk"
    success_message = "Znovu otevření události a zrušení docházky proběhlo úspěšně"
    template_name = "trainings_occurrences/modals/reopen_occurrence.html"


class TrainingOpenOccurrencesOverviewView(
    EventManagePermissionMixin, InsertEventIntoContextData, generic.TemplateView
):
    """
    Displays an overview of open occurrences of a training.

    **Permissions**:

    Users that can manage the training.

    **Path parameters**:

    *   ``event_id`` - training ID
    """

    template_name = "trainings/modals/open_occurrences_overview.html"


class TrainingShowAttendanceView(
    EventManagePermissionMixin,
    MessagesMixin,
    InsertEventIntoContextData,
    generic.TemplateView,
):
    """
    Displays an overview of attendance of a training.

    **Permissions**:

    Users that can manage the training.

    **Path parameters**:

    *   ``event_id`` - training ID
    """

    template_name = "trainings/show_attendance.html"


class TrainingExportParticipantsView(
    EventManagePermissionMixin, InsertEventIntoSelfObjectMixin, generic.View
):
    """
    Exports information about training participants as a CSV file.

    **Permissions**:

    Users that can manage the training.

    **Path parameters**:

    *   ``event_id`` - training ID
    """

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        """:meta private:"""

        approved_persons_id = self.event.trainingparticipantenrollment_set.filter(
            state=ParticipantEnrollment.State.APPROVED
        ).values_list("person_id")
        return export_queryset_csv(
            f"{self.event}_účastníci", Person.objects.filter(id__in=approved_persons_id)
        )


class TrainingExportCoachesView(
    EventManagePermissionMixin, InsertEventIntoSelfObjectMixin, generic.View
):
    """
    Exports information about training coaches as a CSV file.

    **Permissions**:

    Users that can manage the training.

    **Path parameters**:

    *   ``event_id`` - training ID
    """

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        """:meta private:"""

        coaches_id = CoachPositionAssignment.objects.filter(
            training=self.event
        ).values_list("person_id")
        return export_queryset_csv(
            f"{self.event}_trenéři", Person.objects.filter(id__in=coaches_id)
        )


class TrainingExportOrganizersOccurrenceView(
    OccurrenceManagePermissionMixinPK,
    EventOccurrenceIdCheckMixin,
    InsertOccurrenceIntoSelfObjectMixin,
    generic.View,
):
    """
    Exports information about coaches of a training occurrence as a CSV file.

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``pk`` - occurrence ID
    """

    http_method_names = ["get"]
    occurrence_id_key = "pk"

    def get(self, request, *args, **kwargs):
        """:meta private:"""

        coaches_id = CoachOccurrenceAssignment.objects.filter(
            occurrence=self.occurrence, state=TrainingAttendance.PRESENT
        ).values_list("person_id")
        return export_queryset_csv(
            f"{self.occurrence.event}_{date_pretty(self.occurrence.datetime_start)}_trenéři",
            Person.objects.filter(id__in=coaches_id),
        )


class TrainingExportParticipantsOccurrenceView(
    OccurrenceManagePermissionMixinPK,
    EventOccurrenceIdCheckMixin,
    InsertOccurrenceIntoSelfObjectMixin,
    generic.View,
):
    """
    Exports information about participants of a training occurrence as a CSV file.

    **Permissions**:

    Users that can manage the occurrence.

    **Path parameters**:

    *   ``event_id`` - training ID
    *   ``pk`` - occurrence ID
    """

    http_method_names = ["get"]
    occurrence_id_key = "pk"

    def get(self, request, *args, **kwargs):
        """:meta private:"""

        participants_id = TrainingParticipantAttendance.objects.filter(
            occurrence=self.occurrence, state=TrainingAttendance.PRESENT
        ).values_list("person_id")
        return export_queryset_csv(
            f"{self.occurrence.event}_{date_pretty(self.occurrence.datetime_start)}_účastníci",
            Person.objects.filter(id__in=participants_id),
        )
