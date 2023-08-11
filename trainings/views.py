from django.shortcuts import render
from events.views import EventCreateMixin, EventUpdateMixin, EventDetailViewMixin
from django.views import generic
from .forms import TrainingForm


class TrainingDetailView(EventDetailViewMixin):
    template_name = "trainings/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name].extend_2_top_training()
        return context


class TrainingCreateView(generic.CreateView, EventCreateMixin):
    template_name = "trainings/create.html"
    form_class = TrainingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dates"] = context["form"].generate_dates()
        return context


class TrainingUpdateView(generic.UpdateView, EventUpdateMixin):
    template_name = "trainings/edit.html"
    form_class = TrainingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = context[self.context_object_name]
        context["dates"] = context["form"].generate_dates()
        return context
