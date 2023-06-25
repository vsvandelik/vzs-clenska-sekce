from django.urls import reverse_lazy
from .models import Event
from django.views import generic
from .forms import TrainingForm, OneTimeEventForm
from django.contrib.messages.views import SuccessMessageMixin
from .mixin_extensions import FailureMessageMixin


class EventMessagesMixin(SuccessMessageMixin, FailureMessageMixin):
    success_url = reverse_lazy("events:index")


class EventCreateMixin(EventMessagesMixin, generic.FormView):
    success_message = "Událost %(name)s úspěšně přidána."


class EventUpdateMixin(EventMessagesMixin, generic.FormView):
    context_object_name = "event"
    model = Event
    success_message = "Událost %(name)s úspěšně upravena."


class EventIndexView(generic.ListView):
    model = Event
    template_name = "events/index.html"
    context_object_name = "events"

    def get_queryset(self):
        events = Event.objects.filter(parent__isnull=True)
        for event in events:
            event.is_top_training = event.is_top_training()
        return events


class EventDeleteView(EventMessagesMixin, generic.DeleteView):
    model = Event
    template_name = "events/delete.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["children"] = context[
            self.context_object_name
        ].get_children_trainings_sorted()
        return context

    def get_success_message(self, cleaned_data):
        return f"Událost {self.object.name} úspěšně smazána"


class EventDetailView(generic.DetailView):
    model = Event
    template_name = "events/detail.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context[self.context_object_name].is_top_training():
            context[self.context_object_name].extend_2_top_training()
            context["is_top_training"] = True
        return context


class OneTimeEventCreateView(generic.CreateView, EventCreateMixin):
    template_name = "events/create_edit_one_time_event.html"
    form_class = OneTimeEventForm


class OneTimeEventUpdateView(generic.UpdateView, EventUpdateMixin):
    template_name = "events/create_edit_one_time_event.html"
    form_class = OneTimeEventForm


class TrainingCreateView(generic.CreateView, EventCreateMixin):
    template_name = "events/create_edit_training.html"
    form_class = TrainingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dates"] = context["form"].generate_dates()
        return context


class TrainingUpdateView(generic.UpdateView, EventUpdateMixin):
    template_name = "events/create_edit_training.html"
    form_class = TrainingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = context[self.context_object_name]
        event.extend_2_top_training()
        context["dates"] = context["form"].generate_dates()
        return context
