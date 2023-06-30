from django.urls import reverse_lazy
from .models import Event, EventParticipation, Participation
from django.views import generic
from .forms import TrainingForm, OneTimeEventForm, AddDeleteParticipantFromEvent
from django.contrib.messages.views import SuccessMessageMixin
from .mixin_extensions import FailureMessageMixin
from django.shortcuts import get_object_or_404, redirect, reverse
from persons.models import Person


class MessagesMixin(SuccessMessageMixin, FailureMessageMixin):
    pass


class EventMessagesMixin(MessagesMixin):
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
        context["persons"] = Person.objects.all()
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


class SignUpOrRemovePersonFromEvent(MessagesMixin, generic.FormView):
    form_class = AddDeleteParticipantFromEvent

    def get_success_url(self):
        return reverse("events:detail", args=[self.event_id])

    def process_form(self, form, op):
        self.person = Person.objects.get(pk=form.cleaned_data["person_id"])
        self.event_id = form.cleaned_data["event_id"]
        event = Event.objects.get(pk=self.event_id)
        if op == "add":
            try:
                ep = EventParticipation.objects.get(person=self.person, event=event)
                ep.state = Participation.State.APPROVED
            except EventParticipation.DoesNotExist:
                ep = EventParticipation.objects.create(
                    person=self.person, event=event, state=Participation.State.APPROVED
                )
            ep.save()
        else:
            event.participants.remove(self.person)


class SignUpPersonForEvent(SignUpOrRemovePersonFromEvent):
    def get_success_message(self, cleaned_data):
        return f"Osoba {self.person} přihlášena na událost"

    def form_valid(self, form):
        self.process_form(form, "add")
        return super().form_valid(form)


class RemoveParticipantFromEvent(SignUpOrRemovePersonFromEvent):
    def get_success_message(self, cleaned_data):
        return f"Osoba {self.person} odhlášena z události"

    def form_valid(self, form):
        self.process_form(form, "remove")
        return super().form_valid(form)
