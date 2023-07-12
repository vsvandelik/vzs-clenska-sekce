from django.urls import reverse_lazy
from .models import Event, EventParticipation, Participation, EventPositionAssignment
from django.views import generic
from .forms import (
    TrainingForm,
    OneTimeEventForm,
    AddDeleteParticipantFromOneTimeEventForm,
    EventPositionAssignmentForm,
)
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
        events = Event.objects.filter(parent__isnull=True)
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

    def event_position_assignments(self):
        return EventPositionAssignment.objects.filter(event=self.object)


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

    def persons(self):
        return Person.objects.all()

    def event_participation(self):
        return EventParticipation.objects.filter(event=self.object)

    def event_participation_approved(self):
        return self.event_participation().filter(state=Participation.State.APPROVED)

    def event_participation_substitute(self):
        return self.event_participation().filter(state=Participation.State.SUBSTITUTE)


class OneTimeEventCreateView(generic.CreateView, EventCreateMixin):
    template_name = "events/create_edit_one_time_event.html"
    form_class = OneTimeEventForm


class OneTimeEventUpdateView(generic.UpdateView, EventUpdateMixin):
    template_name = "events/create_edit_one_time_event.html"
    form_class = OneTimeEventForm
    invariant = lambda _, e: e.is_one_time_event

    def get(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs["pk"])
        event.set_type()
        if not event.is_one_time_event:
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)


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

    def _process_form(self, form, op, state):
        self.person = Person.objects.get(pk=form.cleaned_data["person_id"])
        self.event_id = form.cleaned_data["event_id"]
        event = Event.objects.get(pk=self.event_id)
        if op == "add":
            try:
                ep = EventParticipation.objects.get(person=self.person, event=event)
                ep.state = state
            except EventParticipation.DoesNotExist:
                ep = EventParticipation.objects.create(
                    person=self.person, event=event, state=state
                )
            ep.save()
        else:
            event.participants.remove(self.person)


class SignUpPersonForOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
    def get_success_message(self, cleaned_data):
        return f"Osoba {self.person} přihlášena na událost"

    def form_valid(self, form):
        self._process_form(form, "add", Participation.State.APPROVED)
        return super().form_valid(form)


class RemoveParticipantFromOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
    def get_success_message(self, cleaned_data):
        return f"Osoba {self.person} odhlášena z události"

    def form_valid(self, form):
        self._process_form(form, "remove", Participation.State.APPROVED)
        return super().form_valid(form)


class AddSubtituteForOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
    def get_success_message(self, cleaned_data):
        return f"Osoba {self.person} přidána mezi náhradníky události"

    def form_valid(self, form):
        self._process_form(form, "add", Participation.State.SUBSTITUTE)
        return super().form_valid(form)


class RemoveSubtituteForOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
    def get_success_message(self, cleaned_data):
        return f"Osoba {self.person} smazána ze seznamu náhradníků události"

    def form_valid(self, form):
        self._process_form(form, "remove", Participation.State.SUBSTITUTE)
        return super().form_valid(form)


class EventPositionAssignmentMixin(MessagesMixin):
    model = EventPositionAssignment
    context_object_name = "position_assignment"

    def get_success_url(self):
        return reverse("events:detail_one_time_event", args=[self.kwargs["event_id"]])


class EventPositionAssignmentCreateView(
    EventPositionAssignmentMixin, generic.CreateView
):
    template_name = "events/create_edit_event_position_assignment.html"
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
    template_name = "events/create_edit_event_position_assignment.html"
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
