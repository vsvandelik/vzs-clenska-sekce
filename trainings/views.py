from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic

from events.models import ParticipantEnrollment
from events.permissions import (
    EventManagePermissionMixin,
    OccurrenceEnrollOrganizerPermissionMixin,
    OccurrenceManagePermissionMixin,
    OccurrenceManagePermissionMixin2,
    OccurrenceUnenrollOrganizerPermissionMixin,
)
from events.views import (
    BulkApproveParticipantsMixin,
    EnrollMyselfParticipantMixin,
    EventCreateMixin,
    EventDetailBaseView,
    EventGeneratesDatesMixin,
    EventOccurrenceIdCheckMixin,
    EventUpdateMixin,
    InsertEventIntoContextData,
    InsertEventIntoModelFormKwargsMixin,
    InsertOccurrenceIntoContextData,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertPositionAssignmentIntoModelFormKwargs,
    OccurrenceDetailBaseView,
    OccurrenceNotOpenedRestrictionMixin,
    OccurrenceOpenRestrictionMixin,
    ParticipantEnrollmentCreateMixin,
    ParticipantEnrollmentDeleteMixin,
    ParticipantEnrollmentUpdateMixin,
    RedirectToEventDetailOnFailureMixin,
    RedirectToEventDetailOnSuccessMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
    RedirectToOccurrenceDetailOnSuccessMixin,
    InsertEventIntoSelfObjectMixin,
    InsertOccurrenceIntoSelfObjectMixin,
)
from one_time_events.permissions import OccurrenceFillAttendancePermissionMixin
from persons.models import Person, get_active_user
from trainings.permissions import (
    OccurrenceEnrollMyselfParticipantPermissionMixin,
    OccurrenceExcuseMyselfOrganizerPermissionMixin,
    OccurrenceExcuseMyselfParticipantPermissionMixin,
    OccurrenceUnenrollMyselfParticipantPermissionMixin,
)
from vzs.mixin_extensions import (
    InsertActivePersonIntoModelFormKwargsMixin,
    InsertRequestIntoModelFormKwargsMixin,
    MessagesMixin,
)
from vzs.settings import CURRENT_DATETIME
from vzs.utils import send_notification_email, date_pretty, export_queryset_csv
from .forms import (
    CancelCoachExcuseForm,
    CancelParticipantExcuseForm,
    CoachAssignmentDeleteForm,
    CoachAssignmentForm,
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
    TrainingParticipantEnrollmentForm,
    TrainingReplaceableForm,
    TrainingUnenrollMyselfOrganizerFromOccurrenceForm,
    TrainingUnenrollMyselfParticipantFromOccurrenceForm,
)
from .models import (
    CoachOccurrenceAssignment,
    CoachPositionAssignment,
    Training,
    TrainingOccurrence,
    TrainingParticipantAttendance,
    TrainingParticipantEnrollment,
    TrainingReplaceabilityForParticipants,
    TrainingAttendance,
)


class TrainingDetailView(EventDetailBaseView):
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
            datetime_start__gte=CURRENT_DATETIME()
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
            datetime_start__lte=CURRENT_DATETIME()
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

        return super().get_context_data(**kwargs)

    def get_template_names(self):
        active_person = self.request.active_person
        active_user = get_active_user(active_person)
        if self.object.can_user_manage(active_user):
            return "trainings/detail.html"
        else:
            return "trainings/detail_for_nonadmin.html"


class TrainingListView(generic.ListView):
    template_name = "trainings/index.html"

    def get_context_data(self, **kwargs):
        active_person = self.request.active_person
        user = get_active_user(active_person)

        enrolled_trainings = Training.objects.filter(
            trainingparticipantenrollment__person=active_person,
        )

        visible_event_pks = [
            event.pk
            for event in Training.objects.all()
            if event.can_user_manage(user)
            or event.can_person_interact_with(active_person)
        ]

        available_trainings = Training.objects.filter(pk__in=visible_event_pks).exclude(
            pk__in=enrolled_trainings
        )

        upcoming_occurrences = TrainingOccurrence.objects.filter(
            datetime_start__gte=CURRENT_DATETIME(), participants=active_person
        ).order_by("datetime_start")
        for occurrence in upcoming_occurrences:
            occurrence.can_excuse = occurrence.can_participant_excuse(active_person)
            participant_attendance = occurrence.get_participant_attendance(
                active_person
            )
            occurrence.excused = (
                participant_attendance
                and participant_attendance.state == TrainingAttendance.EXCUSED
            )

        (
            count_of_trainings_to_replace,
            replaceable_occurrences,
        ) = self.replaceable_occurrences(active_person, enrolled_trainings)

        kwargs.setdefault("upcoming_trainings_occurrences", upcoming_occurrences)
        kwargs.setdefault("enrolled_trainings", enrolled_trainings)
        kwargs.setdefault("available_trainings", available_trainings)
        kwargs.setdefault(
            "count_of_trainings_to_replace", count_of_trainings_to_replace
        )
        kwargs.setdefault("replaceable_occurrences", replaceable_occurrences)

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return []

    def replaceable_occurrences(self, active_person, enrolled_trainings):
        count_of_trainings_to_replace = (
            TrainingParticipantAttendance.count_of_trainings_to_replace(active_person)
        )

        if count_of_trainings_to_replace <= 0:
            return count_of_trainings_to_replace, []

        replaceable_trainings = []

        for enrolled_training in enrolled_trainings:
            replaceable_trainings += enrolled_training.replaces_training_list()

        replaceable_occurrences = (
            TrainingOccurrence.objects.filter(
                datetime_start__gte=CURRENT_DATETIME(), event__in=replaceable_trainings
            )
            .exclude(participants=active_person)
            .order_by("datetime_start")[:10]
        )

        return count_of_trainings_to_replace, replaceable_occurrences


class TrainingCreateView(EventGeneratesDatesMixin, EventCreateMixin):
    template_name = "trainings/create.html"
    form_class = TrainingForm


class TrainingUpdateView(EventGeneratesDatesMixin, EventUpdateMixin):
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


class TrainingWeekdaysSelectionMixin:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("checked_weekdays", self.get_form().checked_weekdays())
        return super().get_context_data(**kwargs)


class TrainingParticipantEnrollmentCreateUpdateMixin(
    EventManagePermissionMixin, TrainingWeekdaysSelectionMixin
):
    model = TrainingParticipantEnrollment
    form_class = TrainingParticipantEnrollmentForm
    event_id_key = "event_id"


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


class CoachAssignmentMixin(
    EventManagePermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
):
    model = CoachPositionAssignment
    context_object_name = "coach_assignment"


class CoachAssignmentCreateUpdateMixin(
    CoachAssignmentMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
):
    form_class = CoachAssignmentForm


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
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    OccurrenceOpenRestrictionMixin,
    generic.FormView,
):
    model = CoachOccurrenceAssignment
    context_object_name = "assignment"


class CancelCoachExcuseView(
    OccurrenceManagePermissionMixin,
    CoachOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = CancelCoachExcuseForm
    template_name = "trainings_occurrences/modals/cancel_coach_excuse.html"
    success_message = "Zrušení omluvenky trenéra proběhlo úspěšně"


class ExcuseMyselfCoachView(
    OccurrenceExcuseMyselfOrganizerPermissionMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
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
    OccurrenceManagePermissionMixin,
    CoachOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = CoachExcuseForm
    template_name = "trainings_occurrences/modals/coach_excuse.html"
    success_message = "Omluvení trenéra proběhlo úspěšně"


class EnrollMyselfOrganizerForOccurrenceView(
    OccurrenceEnrollOrganizerPermissionMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
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
    OccurrenceManagePermissionMixin,
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
    RedirectToOccurrenceDetailOnFailureMixin,
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
    OccurrenceManagePermissionMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    CoachOccurrenceBaseView,
    generic.CreateView,
):
    form_class = CoachOccurrenceAssignmentForm
    template_name = "trainings_occurrences/create_coach_occurrence_assignment.html"
    success_message = "Jednorázový trenér %(person)s přidán"


class EditOneTimeCoachView(
    OccurrenceManagePermissionMixin,
    MessagesMixin,
    RedirectToOccurrenceDetailOnSuccessMixin,
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
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    OccurrenceOpenRestrictionMixin,
    generic.FormView,
):
    model = TrainingParticipantAttendance
    context_object_name = "participant_attendance"


class ExcuseParticipantView(
    OccurrenceManagePermissionMixin,
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = ParticipantExcuseForm
    template_name = "trainings_occurrences/modals/participant_excuse.html"
    success_message = "Omluvení účastníka proběhlo úspěšně"


class CancelParticipantExcuseView(
    OccurrenceManagePermissionMixin,
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = CancelParticipantExcuseForm
    template_name = "trainings_occurrences/modals/cancel_participant_excuse.html"
    success_message = "Zrušení omluvenky účastníka proběhlo úspěšně"


class ExcuseMyselfParticipantView(
    OccurrenceExcuseMyselfParticipantPermissionMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
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
    RedirectToOccurrenceDetailOnFailureMixin,
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = TrainingUnenrollMyselfParticipantFromOccurrenceForm
    template_name = (
        "trainings_occurrences/modals/unenroll_myself_participant_occurrence.html"
    )
    success_message = "Odhlášení jako jednorázový účastník proběhlo úspěšně"


class AddOneTimeParticipantView(
    OccurrenceManagePermissionMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    ParticipantOccurrenceBaseView,
    generic.CreateView,
):
    form_class = TrainingParticipantAttendanceForm
    template_name = "trainings_occurrences/create_one_time_participant.html"
    success_message = "Jednorázový účastník %(person)s přidán"


class OneTimeParticipantDeleteView(
    OccurrenceManagePermissionMixin,
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
    RedirectToOccurrenceDetailOnSuccessMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    EventOccurrenceIdCheckMixin,
    OccurrenceOpenRestrictionMixin,
    generic.CreateView,
):
    form_class = TrainingEnrollMyselfParticipantOccurrenceForm
    success_message = "Přihlášení jako jednorázový účastník proběhlo úspěšně"
    template_name = "trainings_occurrences/detail.html"


class TrainingOccurrenceAttendanceCanBeFilledMixin:
    def dispatch(self, request, *args, **kwargs):
        occurrence = self.get_object()
        if CURRENT_DATETIME() < timezone.localtime(occurrence.datetime_start):
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class TrainingFillAttendanceView(
    OccurrenceFillAttendancePermissionMixin,
    MessagesMixin,
    TrainingOccurrenceAttendanceCanBeFilledMixin,
    RedirectToOccurrenceDetailOnSuccessMixin,
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
    OccurrenceManagePermissionMixin2,
    MessagesMixin,
    OccurrenceNotOpenedRestrictionMixin,
    RedirectToOccurrenceDetailOnSuccessMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
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
    OccurrenceManagePermissionMixin2,
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
    OccurrenceManagePermissionMixin2,
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
