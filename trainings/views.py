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
    TrainingWeekdaysSelectionMixin,
    TrainingParticipantEnrollmentCreateUpdateMixin,
    TrainingOccurrenceAttendanceCanBeFilledMixin,
    InsertAvailableCategoriesIntoFormsKwargsMixin,
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
    def get_context_data(self, **kwargs):
        active_person = self.request.active_person
        trainings_for_replacement_to_choose = (
            Training.objects.filter(
                category=self.object.category,
            )
            .exclude(pk=self.object.pk)
            .exclude(replaceable_training_2__training_1=self.object)
        )

        upcoming_occurrences = self.object.sorted_occurrences_list().filter(
            datetime_start__gte=now(),
            participants=active_person,
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
            datetime_start__lte=now(),
            participants=active_person,
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

        participant_enrollment = self.object.get_participant_enrollment(active_person)

        kwargs.setdefault(
            "trainings_for_replacement", trainings_for_replacement_to_choose
        )
        kwargs.setdefault(
            "selected_replaceable_trainings", selected_replaceable_trainings
        )
        kwargs.setdefault(
            "active_person_participant_enrollment", participant_enrollment
        )
        kwargs.setdefault(
            "active_person_participant_enrolled_weekdays",
            participant_enrollment.participant_weekdays_as_list(),
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
        active_person = self.request.active_person
        active_user = get_active_user(active_person)
        if self.object.can_user_manage(active_user):
            return "trainings/detail_admin.html"
        elif self.object.is_organizer(active_person):
            return "trainings/detail_coach.html"
        else:
            return "trainings/detail_participant.html"

    def _add_coaches_detail_kwargs(self, kwargs):
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
    template_name = "trainings/index.html"

    def get_context_data(self, **kwargs):
        active_person = self.request.active_person

        self._add_participant_kwargs(kwargs, active_person)
        self._add_coaches_kwargs(kwargs, active_person)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return []

    def _add_coaches_kwargs(self, kwargs, active_person):
        regular_trainings = Training.get_unfinished_trainings_by_coach(active_person)
        upcoming_occurrences = TrainingOccurrence.get_upcoming_by_coach(
            active_person, False
        ).all()

        for occurrence in upcoming_occurrences:
            occurrence.excused = occurrence.is_coach_excused(active_person)

        kwargs.setdefault("coach_regular_trainings", regular_trainings)
        kwargs.setdefault("coach_upcoming_occurrences", upcoming_occurrences)

    def _add_participant_kwargs(self, kwargs, active_person):
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
        count_of_trainings_to_replace = (
            TrainingParticipantAttendance.count_of_trainings_to_replace(active_person)
        )

        if count_of_trainings_to_replace <= 0:
            return

        replaceable_trainings = list(enrolled_trainings)

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
            o
            for o in replaceable_occurrences
            if o.can_participant_enroll(active_person)
        ][:10]

        kwargs.setdefault(
            "participant_count_of_trainings_to_replace", count_of_trainings_to_replace
        )
        kwargs.setdefault(
            "participant_replaceable_occurrences", available_replaceable_occurrences
        )


class TrainingAdminListView(TrainingCreatePermissionMixin, EventAdminListMixin):
    template_name = "trainings/list_admin.html"
    context_object_name = "trainings"

    def get(self, request, *args, **kwargs):
        self.filter_form = TrainingsFilterForm(request.GET)
        return super().get(request, *args, **kwargs)

    def get_accessible_events(self):
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
    template_name = "trainings/create.html"
    form_class = TrainingForm


class TrainingUpdateView(
    InsertAvailableCategoriesIntoFormsKwargsMixin,
    EventGeneratesDatesMixin,
    EventUpdateMixin,
):
    template_name = "trainings/edit.html"
    form_class = TrainingForm


class TrainingAddReplaceableTrainingView(
    EventManagePermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    RedirectToEventDetailOnFailureMixin,
    generic.CreateView,
):
    form_class = TrainingReplaceableForm
    success_message = _("Tréninky pro náhrady byl přidán.")
    model = TrainingReplaceabilityForParticipants
    event_id_key = "event_id"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["training_1"] = get_object_or_404(Training, pk=self.kwargs["event_id"])
        return kwargs


class TrainingRemoveReplaceableTrainingView(EventManagePermissionMixin, generic.View):
    http_method_names = ["post"]
    event_id_key = "event_id"

    def post(self, request, event_id, *args, **kwargs):
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
    template_name = "trainings/create_participant_enrollment.html"


class TrainingParticipantEnrollmentUpdateView(
    TrainingParticipantEnrollmentCreateUpdateMixin, ParticipantEnrollmentUpdateMixin
):
    template_name = "trainings/edit_participant_enrollment.html"


class TrainingParticipantEnrollmentDeleteView(ParticipantEnrollmentDeleteMixin):
    template_name = "trainings/modals/delete_participant_enrollment.html"

    def form_valid(self, form):
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
    model = TrainingParticipantEnrollment
    form_class = TrainingEnrollMyselfParticipantForm
    template_name = "trainings/enroll_myself_participant.html"
    success_message = "Přihlášení na trénink proběhlo úspěšně"


class CoachAssignmentCreateView(CoachAssignmentCreateUpdateMixin, generic.CreateView):
    template_name = "trainings/create_coach_assignment.html"
    success_message = "Trenér %(person)s přidán"


class CoachAssignmentUpdateView(CoachAssignmentCreateUpdateMixin, generic.UpdateView):
    template_name = "trainings/edit_coach_assignment.html"
    success_message = "Trenér %(person)s upraven"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["person"] = self.object.person
        return kwargs


class CoachAssignmentDeleteView(CoachAssignmentMixin, generic.UpdateView):
    success_message = "Odhlášení trenéra proběhlo úspěšně"
    template_name = "trainings/modals/delete_coach_assignment.html"
    form_class = CoachAssignmentDeleteForm
    event_id_key = "event_id"


class TrainingBulkApproveParticipantsView(BulkApproveParticipantsMixin):
    form_class = TrainingBulkApproveParticipantsForm


class TrainingOccurrenceDetailView(OccurrenceDetailBaseView):
    model = TrainingOccurrence
    template_name = "trainings_occurrences/detail.html"

    def get_context_data(self, **kwargs):
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
    model = CoachOccurrenceAssignment
    context_object_name = "assignment"


class CancelCoachExcuseView(
    OccurrenceManagePermissionMixinID,
    CoachOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = CancelCoachExcuseForm
    template_name = "trainings_occurrences/modals/cancel_coach_excuse.html"
    success_message = "Zrušení omluvenky trenéra proběhlo úspěšně"


class ExcuseMyselfCoachView(
    OccurrenceExcuseMyselfOrganizerPermissionMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    CoachOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = ExcuseMyselfCoachForm
    template_name = "trainings_occurrences/modals/excuse_myself_coach.html"
    success_message = "Vaše trenérská neúčast byla úspěšně nahlášena"

    def get_object(self, queryset=None):
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
    form_class = TrainingEnrollMyselfOrganizerOccurrenceForm
    success_message = "Přihlášení jako jednorázový trenér proběhlo úspěšně"
    template_name = "trainings_occurrences/detail.html"


class OneTimeCoachDeleteView(
    OccurrenceManagePermissionMixinID,
    CoachOccurrenceBaseView,
    generic.DeleteView,
):
    template_name = "trainings_occurrences/modals/delete_one_time_coach.html"

    def get_success_message(self, cleaned_data):
        return (
            f"Osoba {self.object.person} byla úspěšně odebrána jako jednorázový trenér"
        )

    def form_valid(self, form):
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
    form_class = TrainingUnenrollMyselfOrganizerFromOccurrenceForm
    template_name = (
        "trainings_occurrences/modals/unenroll_myself_organizer_occurrence.html"
    )

    def get_success_message(self, cleaned_data):
        return f"Odhlášení z jednorázové trenérské pozice proběhlo úspěšně"


class AddOneTimeCoachView(
    OccurrenceManagePermissionMixinID,
    InsertOccurrenceIntoModelFormKwargsMixin,
    CoachOccurrenceBaseView,
    generic.CreateView,
):
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
    model = CoachOccurrenceAssignment
    form_class = CoachOccurrenceAssignmentForm
    context_object_name = "assignment"
    template_name = "trainings_occurrences/edit_coach_occurrence_assignment.html"
    success_message = "Přihláska jednorázového trenéra %(person)s upravena"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["occurrence"] = self.object.occurrence
        kwargs["person"] = self.object.person
        return kwargs

    def get_context_data(self, **kwargs):
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
    model = TrainingParticipantAttendance
    context_object_name = "participant_attendance"


class ExcuseParticipantView(
    OccurrenceManagePermissionMixinID,
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = ParticipantExcuseForm
    template_name = "trainings_occurrences/modals/participant_excuse.html"
    success_message = "Omluvení účastníka proběhlo úspěšně"


class CancelParticipantExcuseView(
    OccurrenceManagePermissionMixinID,
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = CancelParticipantExcuseForm
    template_name = "trainings_occurrences/modals/cancel_participant_excuse.html"
    success_message = "Zrušení omluvenky účastníka proběhlo úspěšně"


class ExcuseMyselfParticipantView(
    OccurrenceExcuseMyselfParticipantPermissionMixin,
    RedirectToOccurrenceFallbackEventDetailOnFailureMixin,
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = ExcuseMyselfParticipantForm
    template_name = "trainings_occurrences/modals/excuse_myself_participant.html"
    success_message = "Vaše neúčast jako účastník byla úspěšně nahlášena"

    def get_object(self, queryset=None):
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
    form_class = TrainingParticipantAttendanceForm
    template_name = "trainings_occurrences/create_one_time_participant.html"
    success_message = "Jednorázový účastník %(person)s přidán"


class OneTimeParticipantDeleteView(
    OccurrenceManagePermissionMixinID,
    ParticipantOccurrenceBaseView,
    generic.DeleteView,
):
    template_name = "trainings_occurrences/modals/delete_one_time_participant.html"

    def get_success_message(self, cleaned_data):
        return f"Osoba {self.object.person} byla úspěšně odebrána jako účastník"

    def form_valid(self, form):
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
    form_class = TrainingFillAttendanceForm
    model = TrainingOccurrence
    occurrence_id_key = "pk"
    success_message = "Zapsání docházky proběhlo úspěšně"
    template_name = "trainings_occurrences/attendance.html"

    def get_context_data(self, **kwargs):
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
    form_class = ReopenTrainingOccurrenceForm
    model = TrainingOccurrence
    occurrence_id_key = "pk"
    success_message = "Znovu otevření události a zrušení docházky proběhlo úspěšně"
    template_name = "trainings_occurrences/modals/reopen_occurrence.html"


class TrainingOpenOccurrencesOverviewView(
    EventManagePermissionMixin, InsertEventIntoContextData, generic.TemplateView
):
    template_name = "trainings/modals/open_occurrences_overview.html"


class TrainingShowAttendanceView(
    EventManagePermissionMixin,
    MessagesMixin,
    InsertEventIntoContextData,
    generic.TemplateView,
):
    template_name = "trainings/show_attendance.html"


class TrainingExportParticipantsView(
    EventManagePermissionMixin, InsertEventIntoSelfObjectMixin, generic.View
):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        approved_persons_id = self.event.trainingparticipantenrollment_set.filter(
            state=ParticipantEnrollment.State.APPROVED
        ).values_list("person_id")
        return export_queryset_csv(
            f"{self.event}_účastníci", Person.objects.filter(id__in=approved_persons_id)
        )


class TrainingExportCoachesView(
    EventManagePermissionMixin, InsertEventIntoSelfObjectMixin, generic.View
):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
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
    http_method_names = ["get"]
    occurrence_id_key = "pk"

    def get(self, request, *args, **kwargs):
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
    http_method_names = ["get"]
    occurrence_id_key = "pk"

    def get(self, request, *args, **kwargs):
        participants_id = TrainingParticipantAttendance.objects.filter(
            occurrence=self.occurrence, state=TrainingAttendance.PRESENT
        ).values_list("person_id")
        return export_queryset_csv(
            f"{self.occurrence.event}_{date_pretty(self.occurrence.datetime_start)}_účastníci",
            Person.objects.filter(id__in=participants_id),
        )
