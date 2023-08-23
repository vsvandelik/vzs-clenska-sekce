from django.contrib import messages
from django.db.models import Q
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
)
from vzs.mixin_extensions import MessagesMixin, InsertRequestIntoModelFormKwargsMixin
from .forms import (
    TrainingForm,
    TrainingReplaceableForm,
    TrainingParticipantEnrollmentForm,
)
from .models import (
    Training,
    TrainingReplaceabilityForParticipants,
    TrainingParticipantEnrollment,
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
    MessagesMixin, RedirectToEventDetailOnSuccessMixin, generic.CreateView
):
    form_class = TrainingReplaceableForm
    success_message = _("Tréninky pro náhrady byl přidán.")
    model = TrainingReplaceabilityForParticipants

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["training_1"] = get_object_or_404(Training, pk=self.kwargs["event_id"])
        return kwargs

    def form_invalid(self, form):
        super().form_invalid(form)
        return redirect(reverse("trainings:detail", args=[self.kwargs["event_id"]]))


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


class TrainingParticipantEnrollmentCreateUpdateMixin(
    InsertRequestIntoModelFormKwargsMixin
):
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
    template_name = "trainings/delete_participant_enrollment.html"
