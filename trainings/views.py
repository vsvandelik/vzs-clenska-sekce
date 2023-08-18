from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from events.views import (
    EventCreateMixin,
    EventUpdateMixin,
    EventDetailViewMixin,
    EventGeneratesDatesMixin,
)
from .forms import TrainingForm, TrainingReplaceableForm
from .models import Training, TrainingReplaceabilityForParticipants


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


class TrainingAddReplaceableTrainingView(SuccessMessageMixin, generic.View):
    http_method_names = ["post"]

    def post(self, request, pk, *args, **kwargs):
        form = TrainingReplaceableForm(
            request.POST, training_1=Training.objects.get(pk=pk)
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Tréninky pro náhrady byl přidán.")
        else:
            errors = "".join([" ".join(e) for e in form.errors.values()])
            messages.error(
                request, "Tréninky pro náhrady se nepodařilo přidat. " + errors
            )

        return redirect(reverse("trainings:detail", args=[pk]))
