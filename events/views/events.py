from django.urls import reverse_lazy
from ..models import Event, EventParticipation, Participation
from django.views import generic
from ..forms import (
    TrainingForm,
    OneTimeEventForm,
    AddDeleteParticipantFromOneTimeEventForm,
)
from django.shortcuts import get_object_or_404, redirect, reverse
from persons.models import Person
from ..mixin_extensions import MessagesMixin


class EventConditionMixin:
    def get(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs["pk"])
        event.set_type()
        if not self.event_condition(event):
            return redirect(self.event_condition_failed_redirect_url)
        return super().get(request, *args, **kwargs)


class EventCreateMixin(MessagesMixin, generic.FormView):
    success_message = "Událost %(name)s úspěšně přidána."
    success_url = reverse_lazy("events:index")


class EventUpdateMixin(MessagesMixin, EventConditionMixin, generic.FormView):
    context_object_name = "event"
    model = Event
    success_message = "Událost %(name)s úspěšně upravena."
    event_condition_failed_redirect_url = reverse_lazy("events:index")
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

    def children(self):
        return self.object.get_children_trainings_sorted()

    def get_success_message(self, cleaned_data):
        return f"Událost {self.object.name} úspěšně smazána"


class EventDetailViewMixin(EventConditionMixin, generic.DetailView):
    model = Event
    event_condition_failed_redirect_url = reverse_lazy("events:index")
    context_object_name = "event"


class TrainingDetailView(EventDetailViewMixin):
    template_name = "events/training_detail.html"
    event_condition = lambda _, e: e.is_top_training

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name].extend_2_top_training()
        return context


class OneTimeEventDetailView(EventDetailViewMixin):
    template_name = "events/one_time_event_detail.html"
    event_condition = lambda _, e: e.is_one_time_event

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
    event_condition = lambda _, e: e.is_one_time_event

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
    event_condition = lambda _, e: e.is_top_training

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = context[self.context_object_name]
        event.extend_2_top_training()
        context["dates"] = context["form"].generate_dates()
        return context


class SignUpOrRemovePersonFromOneTimeEventView(MessagesMixin, generic.FormView):
    form_class = AddDeleteParticipantFromOneTimeEventForm

    def get_success_url(self):
        return reverse("events:detail_one_time_event", args=[self.event_id])

    def post(self, request, *args, **kwargs):
        post_extended = request.POST.copy()
        post_extended["event_id"] = kwargs["event_id"]
        form = AddDeleteParticipantFromOneTimeEventForm(post_extended)
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

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
