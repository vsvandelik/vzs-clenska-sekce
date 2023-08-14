from django.urls import reverse_lazy
from .models import (
    Event,
    EventPositionAssignment,
)
from persons.models import Person, PersonType
from django.views import generic

from .forms import (
    EventAgeLimitForm,
    # AddDeleteParticipantFromOneTimeEventForm,
    EventPositionAssignmentForm,
    EventGroupMembershipForm,
    EventAllowedPersonTypeForm,
)
from django.shortcuts import get_object_or_404, reverse
from vzs.mixin_extensions import MessagesMixin
from trainings.models import Training
from one_time_events.models import OneTimeEvent


class EventRestrictionMixin:
    model = Event

    def get_success_url(self):
        id = self.object.id
        if isinstance(self.object, OneTimeEvent):
            return reverse("one_time_events:detail", args=[id])
        elif isinstance(self.object, Training):
            return reverse("trainings:detail", args=[id])


class EventCreateUpdateMixin(MessagesMixin, generic.FormView):
    context_object_name = "event"
    success_url = reverse_lazy("events:index")
    model = Event


class EventCreateMixin(EventCreateUpdateMixin, generic.CreateView):
    success_message = "Událost %(name)s úspěšně přidána."


class EventUpdateMixin(EventCreateUpdateMixin, generic.UpdateView):
    context_object_name = "event"
    success_message = "Událost %(name)s úspěšně upravena."
    success_url = reverse_lazy("events:index")


class EventGeneratesDatesMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dates"] = context["form"].generate_dates()
        return context


class PersonTypeDetailViewMixin:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("available_person_types", Person.Type.choices)
        kwargs.setdefault(
            "person_types_required",
            self.object.allowed_person_types.values_list("person_type", flat=True),
        )
        return super().get_context_data(**kwargs)


class EventDetailViewMixin(PersonTypeDetailViewMixin, generic.DetailView):
    model = Event
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        kwargs.setdefault(
            "event_position_assignments",
            EventPositionAssignment.objects.filter(event=self.object).all(),
        )
        return super().get_context_data(**kwargs)


class EventIndexView(generic.ListView):
    model = Event
    template_name = "events/index.html"
    context_object_name = "events"


class EventDeleteView(MessagesMixin, generic.DeleteView):
    model = Event
    template_name = "events/delete.html"
    context_object_name = "event"
    success_url = reverse_lazy("events:index")

    def get_success_message(self, cleaned_data):
        return f"Událost {self.object.name} úspěšně smazána"


#
#
#
# class SignUpOrRemovePersonFromOneTimeEventView(MessagesMixin, generic.FormView):
#     form_class = AddDeleteParticipantFromOneTimeEventForm
#
#     def get_success_url(self):
#         return reverse("events:detail_one_time_event", args=[self.kwargs["event_id"]])
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["event_id"] = self.kwargs["event_id"]
#         return kwargs
#
#     def _change_save_db(self, person, event):
#         raise ImproperlyConfigured("This method should never be called")
#
#     def _process_form(self, person, event, state):
#         EventOccurrenceParticipation.objects.update_or_create(
#             person=person,
#             event=event,
#             defaults={"person": person, "event": event, "state": state},
#         )
#
#     def form_valid(self, form):
#         person = Person.objects.get(pk=form.cleaned_data["person_id"])
#         event_id = form.cleaned_data["event_id"]
#         event = Event.objects.get(pk=event_id)
#         self._change_save_db(person, event)
#         return super().form_valid(form)
#
#
# class SignUpPersonForOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
#     def get_success_message(self, cleaned_data):
#         return f"Osoba {cleaned_data['person']} přihlášena na událost"
#
#     def _change_save_db(self, person, event):
#         self._process_form(person, event, Participation.State.APPROVED)
#
#
# class RemoveParticipantFromOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
#     def get_success_message(self, cleaned_data):
#         return f"Osoba {cleaned_data['person']} odhlášena z události"
#
#     def _change_save_db(self, person, event):
#         event.participants.remove(person)
#
#
# class AddSubtituteForOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
#     def get_success_message(self, cleaned_data):
#         return f"Osoba {cleaned_data['person']} přidána mezi náhradníky události"
#
#     def _change_save_db(self, person, event):
#         self._process_form(person, event, Participation.State.SUBSTITUTE)
#
#
# class RemoveSubtituteForOneTimeEventView(SignUpOrRemovePersonFromOneTimeEventView):
#     def get_success_message(self, cleaned_data):
#         return f"Osoba {cleaned_data['person']} smazána ze seznamu náhradníků události"
#
#     def _change_save_db(self, person, event):
#         event.participants.remove(person)
#
#
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


class EditAgeLimitView(MessagesMixin, EventRestrictionMixin, generic.UpdateView):
    template_name = "events/edit_age_limit.html"
    form_class = EventAgeLimitForm
    success_message = "Změna věkového omezení uložena"


class EditGroupMembershipView(MessagesMixin, EventRestrictionMixin, generic.UpdateView):
    template_name = "events/edit_group_membership.html"
    form_class = EventGroupMembershipForm
    success_message = "Změna vyžadování skupiny uložena"


class AddRemoveAllowedPersonTypeView(MessagesMixin, generic.UpdateView):
    form_class = EventAllowedPersonTypeForm
    model = Event

    def get_success_url(self):
        return reverse(self.detail, args=[self.kwargs["pk"]])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        instance = Event.objects.get(pk=self.kwargs["pk"])
        self.detail = "trainings:detail"
        if isinstance(instance, OneTimeEvent):
            self.detail = "one_time_events:detail"
        kwargs["instance"] = Event.objects.get(pk=self.kwargs["pk"])
        return kwargs
