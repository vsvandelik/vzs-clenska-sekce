from django.urls import reverse_lazy
from .models import Event
from django.views import generic
from .forms import TrainingForm
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .utils import weekday_pretty


class EventIndexView(generic.ListView):
    model = Event
    template_name = "events/index.html"
    context_object_name = "events"

    def get_queryset(self):
        return Event.objects.filter(parent__isnull=True)


class EventDeleteView(generic.DeleteView):
    model = Event
    template_name = "events/delete.html"
    context_object_name = "event"
    success_url = reverse_lazy("events:index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = kwargs["object"]
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
        return _(f"{self.object} úspěšně smazán.")

    def _error_msg(self):
        return _(f"{self.object} nebyl smazán.")


class EventDetailView(generic.DetailView):
    model = Event
    template_name = "events/detail.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = kwargs["object"]
        if context["event"].is_top_training():
            context["children"] = context["event"].get_children_trainings_sorted()
            context["is_training"] = True
            weekdays = context["event"].get_weekdays_trainings_occur()
            weekdays = list(map(weekday_pretty, weekdays))
            context["weekdays"] = ", ".join(weekdays)
            context["weekly_occurs"] = len(weekdays)
        return context


class TrainingCreateView(generic.CreateView):
    template_name = "events/edit-training.html"
    form_class = TrainingForm
    success_url = reverse_lazy("events:index")

    def form_valid(self, form):
        res = super().form_valid(form)
        messages.success(self.request, self._success_msg())
        return res

    def form_invalid(self, form):
        messages.error(self.request, self._error_msg())
        return super().form_invalid(form)

    def _success_msg(self):
        return _(f"{self.object} úspěšně přidán.")

    def _error_msg(self):
        return _(f"Trénink nebyl přidán.")
