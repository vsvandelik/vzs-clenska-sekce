from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from events.views import (
    EventCreateMixin,
    EventUpdateMixin,
    EventDetailViewMixin,
    EventGeneratesDatesMixin,
    RedirectToEventDetailOnSuccessMixin,
    ParticipantEnrollmentCreateMixin,
    ParticipantEnrollmentDeleteMixin,
    ParticipantEnrollmentUpdateMixin,
    EnrollMyselfParticipantMixin,
    InsertEventIntoModelFormKwargsMixin,
    RedirectToEventDetailOnFailureMixin,
    BulkApproveParticipantsMixin,
    InsertEventIntoContextData,
    OccurrenceDetailViewMixin,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    EventOccurrenceIdCheckMixin,
    InsertPositionAssignmentIntoModelFormKwargs,
)
from vzs.mixin_extensions import (
    MessagesMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
)
from .forms import (
    TrainingForm,
    TrainingReplaceableForm,
    TrainingParticipantEnrollmentForm,
    TrainingEnrollMyselfParticipantForm,
    CoachAssignmentForm,
    TrainingBulkApproveParticipantsForm,
    CancelCoachExcuseForm,
    ExcuseMyselfCoachForm,
    CoachAssignmentDeleteForm,
    CoachExcuseForm,
    TrainingEnrollMyselfOrganizerOccurrenceForm,
    TrainingUnenrollMyselfOrganizerFromOccurrenceForm,
    CoachOccurrenceAssignmentForm,
    ParticipantExcuseForm,
    CancelParticipantExcuseForm,
    ExcuseMyselfParticipantForm,
    TrainingUnenrollMyselfParticipantFromOccurrenceForm,
    TrainingParticipantAttendanceForm,
    TrainingEnrollMyselfParticipantOccurrenceForm,
)
from .models import (
    Training,
    TrainingReplaceabilityForParticipants,
    TrainingParticipantEnrollment,
    CoachPositionAssignment,
    TrainingOccurrence,
    CoachOccurrenceAssignment,
    TrainingParticipantAttendance,
)


class TrainingDetailView(EventDetailViewMixin):
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


class TrainingBulkApproveParticipantsView(BulkApproveParticipantsMixin):
    form_class = TrainingBulkApproveParticipantsForm


class TrainingOccurrenceDetailView(OccurrenceDetailViewMixin):
    model = TrainingOccurrence
    template_name = "occurrences/detail.html"

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


class CancelCoachExcuseView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    generic.UpdateView,
):
    form_class = CancelCoachExcuseForm
    model = CoachOccurrenceAssignment
    context_object_name = "assignment"
    template_name = "occurrences/modals/cancel_coach_excuse.html"
    success_message = "Zrušení omluvenky trenéra proběhlo úspěšně"


class CoachOccurrenceViewMixin(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    generic.FormView,
):
    model = CoachOccurrenceAssignment


class ExcuseMyselfCoachView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
    EventOccurrenceIdCheckMixin,
    generic.UpdateView,
):
    form_class = ExcuseMyselfCoachForm
    model = CoachOccurrenceAssignment
    template_name = "occurrences/modals/excuse_myself_coach.html"
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
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    generic.UpdateView,
):
    form_class = CoachExcuseForm
    model = CoachOccurrenceAssignment
    context_object_name = "assignment"
    template_name = "occurrences/modals/coach_excuse.html"
    success_message = "Omluvení trenéra proběhlo úspěšně"


class EnrollMyselfOrganizerForOccurrenceView(
    MessagesMixin,
    RedirectToOccurrenceDetailOnSuccessMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertPositionAssignmentIntoModelFormKwargs,
    EventOccurrenceIdCheckMixin,
    generic.CreateView,
):
    form_class = TrainingEnrollMyselfOrganizerOccurrenceForm
    success_message = "Přihlášení jako jednorázový trenér proběhlo úspěšně"
    template_name = "occurrences/detail.html"


class OneTimeCoachDeleteView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    generic.DeleteView,
):
    context_object_name = "assignment"
    model = CoachOccurrenceAssignment
    template_name = "occurrences/modals/delete_one_time_coach.html"

    def get_success_message(self, cleaned_data):
        return (
            f"Osoba {self.object.person} byla úspěšně odebrána jako jednorázový trenér"
        )


class UnenrollMyselfOrganizerFromOccurrenceView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
    EventOccurrenceIdCheckMixin,
    generic.UpdateView,
):
    context_object_name = "assignment"
    model = CoachOccurrenceAssignment
    form_class = TrainingUnenrollMyselfOrganizerFromOccurrenceForm
    template_name = "occurrences/modals/unenroll_myself_organizer_occurrence.html"

    def get_success_message(self, cleaned_data):
        return f"Odhlášení z jednorázové trenérské pozice proběhlo úspěšně"


class AddOneTimeCoachView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoModelFormKwargsMixin,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    generic.CreateView,
):
    model = CoachOccurrenceAssignment
    form_class = CoachOccurrenceAssignmentForm
    template_name = "occurrences/create_coach_occurrence_assignment.html"
    success_message = "Jednorázový trenér %(person)s přidán"


class EditOneTimeCoachView(
    MessagesMixin,
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    generic.UpdateView,
):
    model = CoachOccurrenceAssignment
    form_class = CoachOccurrenceAssignmentForm
    context_object_name = "assignment"
    template_name = "occurrences/edit_coach_occurrence_assignment.html"
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


class ExcuseParticipantView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    generic.UpdateView,
):
    form_class = ParticipantExcuseForm
    model = TrainingParticipantAttendance
    context_object_name = "participant_attendance"
    template_name = "occurrences/modals/participant_excuse.html"
    success_message = "Omluvení účastníka proběhlo úspěšně"


class CancelParticipantExcuseView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    generic.UpdateView,
):
    form_class = CancelParticipantExcuseForm
    model = TrainingParticipantAttendance
    context_object_name = "participant_attendance"
    template_name = "occurrences/modals/cancel_participant_excuse.html"
    success_message = "Zrušení omluvenky účastníka proběhlo úspěšně"


class ExcuseMyselfParticipantView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
    EventOccurrenceIdCheckMixin,
    generic.UpdateView,
):
    form_class = ExcuseMyselfParticipantForm
    model = TrainingParticipantAttendance
    template_name = "occurrences/modals/excuse_myself_participant.html"
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
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
    EventOccurrenceIdCheckMixin,
    generic.UpdateView,
):
    context_object_name = "participant_attendance"
    model = TrainingParticipantAttendance
    form_class = TrainingUnenrollMyselfParticipantFromOccurrenceForm
    template_name = "occurrences/modals/unenroll_myself_participant_occurrence.html"
    success_message = "Odhlášení jako jednorázový účastník proběhlo úspěšně"


class AddOneTimeParticipantView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    EventOccurrenceIdCheckMixin,
    generic.CreateView,
):
    model = TrainingParticipantAttendance
    form_class = TrainingParticipantAttendanceForm
    template_name = "occurrences/create_one_time_participant.html"
    success_message = "Jednorázový účastník %(person)s přidán"


class OneTimeParticipantDeleteView(
    MessagesMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    RedirectToOccurrenceDetailOnSuccessMixin,
    EventOccurrenceIdCheckMixin,
    generic.DeleteView,
):
    context_object_name = "participant_attendance"
    model = TrainingParticipantAttendance
    template_name = "occurrences/modals/delete_one_time_participant.html"

    def get_success_message(self, cleaned_data):
        return f"Osoba {self.object.person} byla úspěšně odebrána jako účastník"


class EnrollMyselfParticipantFromOccurrenceView(
    MessagesMixin,
    RedirectToOccurrenceDetailOnSuccessMixin,
    RedirectToOccurrenceDetailOnFailureMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
    InsertOccurrenceIntoModelFormKwargsMixin,
    EventOccurrenceIdCheckMixin,
    generic.CreateView,
):
    form_class = TrainingEnrollMyselfParticipantOccurrenceForm
    success_message = "Přihlášení jako jednorázový účastník proběhlo úspěšně"
    template_name = "occurrences/detail.html"
