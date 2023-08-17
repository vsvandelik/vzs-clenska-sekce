from events.views import (
    EventCreateMixin,
    EventDetailViewMixin,
    EventUpdateMixin,
    EventGeneratesDatesMixin,
    EventRestrictionMixin,
)
from vzs.mixin_extensions import InsertRequestIntoModelFormKwargsMixin
from .forms import OneTimeEventForm, TrainingCategoryForm
from django.views import generic
from vzs.mixin_extensions import MessagesMixin


class OneTimeEventDetailView(EventDetailViewMixin):
    template_name = "one_time_events/detail.html"

    # def get_context_data(self, **kwargs):
    #     participants = OneTimeEventParticipantEnrollment
    #     kwargs.setdefault(
    #         "participants_approved",
    #         self.object.allowed_person_types.values_list("person_type", flat=True),
    #     )
    #     return super().get_context_data(**kwargs)


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
