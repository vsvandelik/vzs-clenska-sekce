from django.urls import reverse_lazy
from .models import Event, EventParticipation, Participation, EventPositionAssignment
from django.views import generic
from .forms import (
    TrainingForm,
    OneTimeEventForm,
    AddDeleteParticipantFromOneTimeEventForm,
    EventPositionAssignmentForm,
    MinAgeForm,
)
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect, reverse
from persons.models import Person
from .mixin_extensions import MessagesMixin, InvariantMixin


class EventCreateMixin(MessagesMixin, generic.FormView):
    success_message = "Událost %(name)s úspěšně přidána."
    success_url = reverse_lazy("events:index")


class EventUpdateMixin(MessagesMixin, InvariantMixin, generic.FormView):
    context_object_name = "event"
    model = Event
    success_message = "Událost %(name)s úspěšně upravena."
    invariant_failed_redirect_url = reverse_lazy("events:index")
    success_url = reverse_lazy("events:index")


class EventIndexView(generic.ListView):
    model = Event
    template_name = "events/index.html"
    context_object_name = "events"

    def get_queryset(self):
        events = Event.one_time_events.all() | Event.parent_trainings.all()
        for event in events:
            event.set_type()
        return events


class EventDeleteView(MessagesMixin, generic.DeleteView):
    model = Event
    template_name = "events/delete.html"
    context_object_name = "event"
    success_url = reverse_lazy("events:index")

    def get_success_message(self, cleaned_data):
        return f"Událost {self.object.name} úspěšně smazána"


class EventDetailViewMixin(InvariantMixin, generic.DetailView):
    model = Event
    invariant_failed_redirect_url = reverse_lazy("events:index")
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        kwargs.setdefault(
            "event_position_assignments",
            EventPositionAssignment.objects.filter(event=self.object).all(),
        )
        return super().get_context_data(**kwargs)


class TrainingDetailView(EventDetailViewMixin):
    template_name = "events/training_detail.html"
    invariant = lambda _, e: e.is_top_training

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name].extend_2_top_training()
        return context


class OneTimeEventDetailView(EventDetailViewMixin):
    template_name = "events/one_time_event_detail.html"
    invariant = lambda _, e: e.is_one_time_event

    def get_context_data(self, **kwargs):
        kwargs.setdefault("persons", Person.objects.all())
        kwargs.setdefault(
            "event_participation",
            EventParticipation.objects.filter(event=self.object).all(),
        )
        kwargs.setdefault(
            "event_participation_approved",
            EventParticipation.objects.filter(
                event=self.object, state=Participation.State.APPROVED
            ),
        )
        kwargs.setdefault(
            "event_participation_substitute",
            EventParticipation.objects.filter(
                event=self.object, state=Participation.State.SUBSTITUTE
            ),
        )
        return super().get_context_data(**kwargs)


class OneTimeEventCreateView(generic.CreateView, EventCreateMixin):
    template_name = "events/create_one_time_event.html"
    form_class = OneTimeEventForm


class OneTimeEventUpdateView(generic.UpdateView, EventUpdateMixin):
    template_name = "events/edit_one_time_event.html"
    form_class = OneTimeEventForm
    invariant = lambda _, e: e.is_one_time_event

    def get(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs["pk"])
        event.set_type()
        if not event.is_one_time_event:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)


class TrainingCreateView(generic.CreateView, EventCreateMixin):
    template_name = "events/create_training.html"
    form_class = TrainingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dates"] = context["form"].generate_dates()
        return context


class TrainingUpdateView(generic.UpdateView, EventUpdateMixin):
    template_name = "events/edit_training.html"
    form_class = TrainingForm
    invariant = lambda _, e: e.is_top_training

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = context[self.context_object_name]
        event.extend_2_top_training()
        context["dates"] = context["form"].generate_dates()
        return context


class SignUpOrRemovePersonFromOneTimeEventView(MessagesMixin, generic.FormView):
    form_class = AddDeleteParticipantFromOneTimeEventForm

    def get_success_url(self):
        return reverse("events:detail_one_time_event", args=[self.kwargs["event_id"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event_id"] = self.kwargs["event_id"]
        return kwargs

    def _change_save_db(self, person, event):
        raise ImproperlyConfigured("This method should never be called")

    def _process_form(self, person, event, state):
        EventParticipation.objects.update_or_create(
            person=person,
            event=event,
            defaults={"person": person, "event": event, "state": state},
        )

    def form_valid(self, form):
        person = Person.objects.get(pk=form.cleaned_data["person_id"])
        event_id = form.cleaned_data["event_id"]
        event = Event.objects.get(pk=event_id)
        self._change_save_db(person, event)
        return super().form_valid(form)


class SignUpPersonForOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
    def get_success_message(self, cleaned_data):
        return f"Osoba {cleaned_data['person']} přihlášena na událost"

    def _change_save_db(self, person, event):
        self._process_form(person, event, Participation.State.APPROVED)


class RemoveParticipantFromOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
    def get_success_message(self, cleaned_data):
        return f"Osoba {cleaned_data['person']} odhlášena z události"

    def _change_save_db(self, person, event):
        event.participants.remove(person)


class AddSubtituteForOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
    def get_success_message(self, cleaned_data):
        return f"Osoba {cleaned_data['person']} přidána mezi náhradníky události"

    def _change_save_db(self, person, event):
        self._process_form(person, event, Participation.State.SUBSTITUTE)


class RemoveSubtituteForOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
    def get_success_message(self, cleaned_data):
        return f"Osoba {cleaned_data['person']} smazána ze seznamu náhradníků události"

    def _change_save_db(self, person, event):
        event.participants.remove(person)


class EventPositionAssignmentMixin(MessagesMixin):
    model = EventPositionAssignment
    context_object_name = "position_assignment"

    def get_success_url(self):
        return reverse("events:detail_one_time_event", args=[self.kwargs["event_id"]])


class EventPositionAssignmentCreateView(
    EventPositionAssignmentMixin, generic.CreateView
):
    template_name = "events/create_event_position_assignment.html"
    form_class = EventPositionAssignmentForm
    success_message = "Organizátorská pozice %(position)s přidána"

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=kwargs["event_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.event
        return kwargs


class EventPositionAssignmentUpdateView(
    EventPositionAssignmentMixin, generic.UpdateView
):
    template_name = "events/edit_event_position_assignment.html"
    success_message = "Organizátorská pozice %(position)s upravena"
    form_class = EventPositionAssignmentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["position"] = self.object.position
        kwargs["event"] = self.object.event
        return kwargs


class EventPositionAssignmentDeleteView(
    EventPositionAssignmentMixin, generic.DeleteView
):
    template_name = "events/delete_event_position_assignment.html"

    def get_success_message(self, cleaned_data):
        return f"Organizátorská pozice {self.object.position} smazána"


class EditMinAgeView(MessagesMixin, generic.UpdateView):
    template_name = "events/edit_min_age.html"
    model = Event
    form_class = MinAgeForm
    success_message = "Změna věkového omezení uložena"

    def get_success_url(self):
        self.object.set_type()
        if self.object.is_one_time_event:
            return reverse("events:detail_one_time_event", args=[self.object.id])
        return reverse("events:detail_training", args=[self.object.id])
