from datetime import datetime

from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic

from events.views import (
    BulkApproveParticipantsMixin,
    EnrollMyselfParticipantMixin,
    EventCreateMixin,
    EventDetailBaseView,
    EventGeneratesDatesMixin,
    EventUpdateMixin,
    InsertEventIntoContextData,
    InsertEventIntoModelFormKwargsMixin,
    InsertOccurrenceIntoContextData,
    OccurrenceDetailBaseView,
    ParticipantEnrollmentCreateMixin,
    ParticipantEnrollmentDeleteMixin,
    ParticipantEnrollmentUpdateMixin,
    RedirectToEventDetailOnFailureMixin,
    RedirectToEventDetailOnSuccessMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    EventOccurrenceIdCheckMixin,
    InsertPositionAssignmentIntoModelFormKwargs,
    OccurrenceOpenRestrictionMixin,
    RedirectToOccurrenceDetailOnSuccessMixin,
)
from vzs.mixin_extensions import (
    InsertActivePersonIntoModelFormKwargsMixin,
    InsertRequestIntoModelFormKwargsMixin,
    MessagesMixin,
)
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
    TrainingBulkApproveParticipantsForm,
    TrainingEnrollMyselfOrganizerOccurrenceForm,
    TrainingEnrollMyselfParticipantForm,
    TrainingEnrollMyselfParticipantOccurrenceForm,
    TrainingFillAttendanceForm,
    ReopenTrainingOccurrenceForm,
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
)


class TrainingDetailView(EventDetailBaseView):
    template_name = "trainings/detail.html"

    def get_context_data(self, **kwargs):
        trainings_for_replacement_to_choose = (
            Training.objects.filter(
                category=self.object.category,
            )
            .exclude(pk=self.object.pk)
            .exclude(replaceable_training_2__training_1=self.object)
        )

        selected_replaceable_trainings = (
            TrainingReplaceabilityForParticipants.objects.filter(training_1=self.object)
        )

        kwargs.setdefault(
            "trainings_for_replacement", trainings_for_replacement_to_choose
        )
        kwargs.setdefault(
            "selected_replaceable_trainings", selected_replaceable_trainings
        )
        return super().get_context_data(**kwargs)


class TrainingCreateView(EventGeneratesDatesMixin, EventCreateMixin):
    template_name = "trainings/create.html"
    form_class = TrainingForm


class TrainingUpdateView(EventGeneratesDatesMixin, EventUpdateMixin):
    template_name = "trainings/edit.html"
    form_class = TrainingForm


class TrainingAddReplaceableTrainingView(
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    RedirectToEventDetailOnFailureMixin,
    generic.CreateView,
):
    form_class = TrainingReplaceableForm
    success_message = _("Tréninky pro náhrady byl přidán.")
    model = TrainingReplaceabilityForParticipants

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["training_1"] = get_object_or_404(Training, pk=self.kwargs["event_id"])
        return kwargs


class TrainingRemoveReplaceableTrainingView(generic.View):
    http_method_names = ["post"]

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


class TrainingParticipantEnrollmentCreateUpdateMixin(TrainingWeekdaysSelectionMixin):
    model = TrainingParticipantEnrollment
    form_class = TrainingParticipantEnrollmentForm


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


class TrainingEnrollMyselfParticipantView(
    TrainingWeekdaysSelectionMixin, EnrollMyselfParticipantMixin
):
    model = TrainingParticipantEnrollment
    form_class = TrainingEnrollMyselfParticipantForm
    template_name = "trainings/enroll_myself_participant.html"
    success_message = "Přihlášení na trénink proběhlo úspěšně"


class CoachAssignmentMixin(
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
    CoachOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = CancelCoachExcuseForm
    template_name = "trainings_occurrences/modals/cancel_coach_excuse.html"
    success_message = "Zrušení omluvenky trenéra proběhlo úspěšně"


class ExcuseMyselfCoachView(
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
    CoachOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = CoachExcuseForm
    template_name = "trainings_occurrences/modals/coach_excuse.html"
    success_message = "Omluvení trenéra proběhlo úspěšně"


class EnrollMyselfOrganizerForOccurrenceView(
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
    CoachOccurrenceBaseView,
    generic.DeleteView,
):
    template_name = "trainings_occurrences/modals/delete_one_time_coach.html"

    def get_success_message(self, cleaned_data):
        return (
            f"Osoba {self.object.person} byla úspěšně odebrána jako jednorázový trenér"
        )


class UnenrollMyselfOrganizerFromOccurrenceView(
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
    InsertOccurrenceIntoModelFormKwargsMixin,
    CoachOccurrenceBaseView,
    generic.CreateView,
):
    form_class = CoachOccurrenceAssignmentForm
    template_name = "trainings_occurrences/create_coach_occurrence_assignment.html"
    success_message = "Jednorázový trenér %(person)s přidán"


class EditOneTimeCoachView(
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
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = ParticipantExcuseForm
    template_name = "trainings_occurrences/modals/participant_excuse.html"
    success_message = "Omluvení účastníka proběhlo úspěšně"


class CancelParticipantExcuseView(
    ParticipantOccurrenceBaseView,
    generic.UpdateView,
):
    form_class = CancelParticipantExcuseForm
    template_name = "trainings_occurrences/modals/cancel_participant_excuse.html"
    success_message = "Zrušení omluvenky účastníka proběhlo úspěšně"


class ExcuseMyselfParticipantView(
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
    InsertOccurrenceIntoModelFormKwargsMixin,
    ParticipantOccurrenceBaseView,
    generic.CreateView,
):
    form_class = TrainingParticipantAttendanceForm
    template_name = "trainings_occurrences/create_one_time_participant.html"
    success_message = "Jednorázový účastník %(person)s přidán"


class OneTimeParticipantDeleteView(
    ParticipantOccurrenceBaseView,
    generic.DeleteView,
):
    template_name = "trainings_occurrences/modals/delete_one_time_participant.html"

    def get_success_message(self, cleaned_data):
        return f"Osoba {self.object.person} byla úspěšně odebrána jako účastník"


class EnrollMyselfParticipantFromOccurrenceView(
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
        if datetime.now(tz=timezone.get_default_timezone()) < occurrence.datetime_start:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class TrainingFillAttendanceView(
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
    MessagesMixin,
    TrainingOccurrenceAttendanceCanBeFilledMixin,
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
    template_name = "trainings_occurrences/modals/reopen_training.html"


class OpenOccurrencesOverviewView(InsertEventIntoContextData, generic.TemplateView):
    template_name = "trainings/modals/open_occurrences_overview.html"
