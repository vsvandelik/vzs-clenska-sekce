from django.http import Http404
from django.utils import timezone

from events.permissions import EventManagePermissionMixin
from events.views import (
    RedirectToEventDetailOnSuccessMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
)
from persons.models import get_active_user
from trainings.forms import TrainingParticipantEnrollmentForm, CoachAssignmentForm
from trainings.models import TrainingParticipantEnrollment, CoachPositionAssignment
from trainings.permissions import TrainingCreatePermissionMixin
from vzs.mixin_extensions import MessagesMixin
from vzs.utils import now


class TrainingWeekdaysSelectionMixin:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("checked_weekdays", self.get_form().checked_weekdays())
        return super().get_context_data(**kwargs)


class TrainingOccurrenceAttendanceCanBeFilledMixin:
    def dispatch(self, request, *args, **kwargs):
        occurrence = self.get_object()
        if now() < timezone.localtime(occurrence.datetime_start):
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class TrainingParticipantEnrollmentCreateUpdateMixin(
    EventManagePermissionMixin, TrainingWeekdaysSelectionMixin
):
    model = TrainingParticipantEnrollment
    form_class = TrainingParticipantEnrollmentForm
    event_id_key = "event_id"


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


class InsertAvailableCategoriesIntoFormsKwargsMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        active_person = self.request.active_person
        active_user = get_active_user(active_person)

        available_categories = []
        for category in TrainingCreatePermissionMixin.permissions_formula_GET:
            if active_user.has_perm(category[0]):
                available_categories.append(category[0])

        kwargs["available_categories"] = available_categories
        return kwargs
