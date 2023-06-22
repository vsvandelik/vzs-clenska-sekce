from django.urls import reverse_lazy
from .models import Event
from django.views import generic
from .forms import TrainingForm, OneTimeEventForm
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .utils import weekday_pretty, days_shortcut_list, days_pretty_list


class EventFormBase(generic.FormView):
    success_url = reverse_lazy("events:index")

    def form_valid(self, form):
        res = super().form_valid(form)
        messages.success(self.request, self._success_msg())
        return res

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        return super().form_invalid(form)


class EventCreateBase(EventFormBase):
    def _success_msg(self):
        return _(f"Událost {self.object} úspěšně přidána.")


class EventUpdateBase(EventFormBase):
    context_object_name = "event"
    model = Event

    def _success_msg(self):
        return _(f"Událost {self.object} úspěšně upravena.")


class EventIndexView(generic.ListView):
    model = Event
    template_name = "events/index.html"
    context_object_name = "events"

    def get_queryset(self):
        events = Event.objects.filter(parent__isnull=True)
        for event in events:
            event.is_top_training = event.is_top_training()
        return events


class EventDeleteView(generic.DeleteView):
    model = Event
    template_name = "events/delete.html"
    context_object_name = "event"
    success_url = reverse_lazy("events:index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["children"] = context[
            self.context_object_name
        ].get_children_trainings_sorted()
        return context

    def form_valid(self, form):
        messages.success(self.request, self._success_msg())
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, self._error_msg())
        return super().form_invalid(form)

    def _success_msg(self):
        return _(f"událost {self.object} úspěšně smazána.")

    def _error_msg(self):
        return _(f"událost {self.object} nebyla smazána.")


class EventDetailView(generic.DetailView):
    model = Event
    template_name = "events/detail.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context[self.context_object_name].is_top_training():
            context[self.context_object_name].extend_2_top_training()
            context["is_top_training"] = True
            weekdays = list(
                map(weekday_pretty, context[self.context_object_name].weekdays)
            )
            context["weekdays"] = ", ".join(weekdays)
            context["weekdays_count"] = len(weekdays)
        return context


class OneTimeEventCreateView(generic.CreateView, EventCreateBase):
    template_name = "events/create_edit_one_time_event.html"
    form_class = OneTimeEventForm


class OneTimeEventUpdateView(generic.UpdateView, EventUpdateBase):
    template_name = "events/create_edit_one_time_event.html"
    form_class = OneTimeEventForm


class TrainingCreateView(generic.CreateView, EventCreateBase):
    template_name = "events/create_edit_training.html"
    form_class = TrainingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["days"] = days_shortcut_list()
        context["days_pretty"] = days_pretty_list()
        context["dates"] = context["form"].generate_dates()
        return context


class TrainingUpdateView(generic.UpdateView, EventUpdateBase):
    template_name = "events/create_edit_training.html"
    form_class = TrainingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = context[self.context_object_name]
        event.extend_2_top_training()
        context["days"] = days_shortcut_list()
        context["days_pretty"] = days_pretty_list()
        context["dates"] = context["form"].generate_dates()
        context["weekday_disable"] = {}
        for weekday in context["dates"]:
            context["weekday_disable"][weekday] = (
                sum(map(lambda x: x[1], context["dates"][weekday])) == 1
            )
        return context
