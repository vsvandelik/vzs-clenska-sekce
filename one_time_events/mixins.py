from django.http import Http404

from events.permissions import (
    EventManagePermissionMixin,
    OccurrenceManagePermissionMixin,
)
from events.views import (
    RedirectToEventDetailOnSuccessMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
)
from one_time_events.forms import OneTimeEventParticipantEnrollmentForm
from one_time_events.models import OneTimeEventParticipantEnrollment
from one_time_events.permissions import OneTimeEventCreatePermissionMixin
from persons.models import get_active_user
from vzs.mixins import InsertRequestIntoModelFormKwargsMixin, MessagesMixin
from vzs.utils import today


class OneTimeEventParticipantEnrollmentCreateUpdateMixin(
    EventManagePermissionMixin, InsertRequestIntoModelFormKwargsMixin
):
    model = OneTimeEventParticipantEnrollment
    form_class = OneTimeEventParticipantEnrollmentForm
    event_id_key = "event_id"


class OrganizerForOccurrenceMixin(
    OccurrenceManagePermissionMixin,
    RedirectToEventDetailOnSuccessMixin,
    MessagesMixin,
):
    pass


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


class OneTimeEventOccurrenceAttendanceCanBeFilledMixin:
    def dispatch(self, request, *args, **kwargs):
        occurrence = self.get_object()
        if today() < occurrence.date:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class InsertAvailableCategoriesIntoFormsKwargsMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        active_person = self.request.active_person
        active_user = get_active_user(active_person)

        available_categories = []
        for category in OneTimeEventCreatePermissionMixin.permissions_formula_GET:
            if active_user.has_perm(category[0]):
                available_categories.append(category[0])

        kwargs["available_categories"] = available_categories
        return kwargs
