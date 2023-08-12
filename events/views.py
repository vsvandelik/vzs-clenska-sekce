from django.urls import reverse_lazy
from .models import (
    Event,
    EventPositionAssignment,
)
from persons.models import Person, PersonType
from django.views import generic

# from .forms import (
#     TrainingForm,
#     OneTimeEventForm,
#     AddDeleteParticipantFromOneTimeEventForm,
#     EventPositionAssignmentForm,
#     MinAgeForm,
#     GroupMembershipForm,
#     PersonTypeEventForm,
# )
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect, reverse
from .mixin_extensions import MessagesMixin


class EventCreateUpdateMixin(MessagesMixin, generic.FormView):
    context_object_name = "event"
    success_url = reverse_lazy("events:index")
    model = Event


class EventCreateMixin(EventCreateUpdateMixin):
    success_message = "Událost %(name)s úspěšně přidána."


class EventUpdateMixin(EventCreateUpdateMixin):
    context_object_name = "event"
    success_message = "Událost %(name)s úspěšně upravena."
    success_url = reverse_lazy("events:index")


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


class EventDetailViewMixin(generic.DetailView):
    model = Event
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        kwargs.setdefault(
            "event_position_assignments",
            EventPositionAssignment.objects.filter(event=self.object).all(),
        )
        kwargs.setdefault("available_person_types", Person.Type.choices)
        kwargs.setdefault(
            "person_types_required",
            self.object.allowed_person_types.values_list("person_type", flat=True),
        )
        return super().get_context_data(**kwargs)


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
# class EventPositionAssignmentMixin(MessagesMixin):
#     model = EventPositionAssignment
#     context_object_name = "position_assignment"
#
#     def get_success_url(self):
#         return reverse("events:detail_one_time_event", args=[self.kwargs["event_id"]])
#
#
# class EventPositionAssignmentCreateView(
#     EventPositionAssignmentMixin, generic.CreateView
# ):
#     template_name = "events/create_event_position_assignment.html"
#     form_class = EventPositionAssignmentForm
#     success_message = "Organizátorská pozice %(position)s přidána"
#
#     def dispatch(self, request, *args, **kwargs):
#         self.event = get_object_or_404(Event, pk=kwargs["event_id"])
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["event"] = self.event
#         return kwargs
#
#
# class EventPositionAssignmentUpdateView(
#     EventPositionAssignmentMixin, generic.UpdateView
# ):
#     template_name = "events/edit_event_position_assignment.html"
#     success_message = "Organizátorská pozice %(position)s upravena"
#     form_class = EventPositionAssignmentForm
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["position"] = self.object.position
#         kwargs["event"] = self.object.event
#         return kwargs
#
#
# class EventPositionAssignmentDeleteView(
#     EventPositionAssignmentMixin, generic.DeleteView
# ):
#     template_name = "events/delete_event_position_assignment.html"
#
#     def get_success_message(self, cleaned_data):
#         return f"Organizátorská pozice {self.object.position} smazána"
#
#
# class EventRestrictionMixin(MessagesMixin):
#     model = Event
#
#     def get_success_url(self):
#         if "event_id" in self.kwargs:
#             self.object = Event.objects.get(pk=self.kwargs["event_id"])
#         self.object.set_type()
#         viewname = "events:detail_training"
#         if self.object.is_one_time_event:
#             viewname = "events:detail_one_time_event"
#         return reverse(viewname, args=[self.object.id])
#
#
# class EditMinAgeView(EventRestrictionMixin, generic.UpdateView):
#     template_name = "events/edit_min_age.html"
#     form_class = MinAgeForm
#     success_message = "Změna věkového omezení uložena"
#
#
# class EditGroupMembershipView(EventRestrictionMixin, generic.UpdateView):
#     template_name = "common_components/edit_group_membership.html"
#     form_class = GroupMembershipForm
#     success_message = "Změna vyžadování skupiny uložena"
#
#
# class AddOrRemoveAllowedPersonTypeToEventView(EventRestrictionMixin, generic.FormView):
#     form_class = PersonTypeEventForm
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["event_id"] = self.kwargs["event_id"]
#         return kwargs
#
#     def _change_db(self, position):
#         raise ImproperlyConfigured("This method should never be called")
#
#     def form_valid(self, form):
#         event = form.cleaned_data["event"]
#         person_type = form.cleaned_data["person_type"]
#         self.person_type_obj, _ = PersonType.objects.get_or_create(
#             person_type=person_type, defaults={"person_type": person_type}
#         )
#         self._change_db(event)
#         event.save()
#         return super().form_valid(form)
#
#
# class AddAllowedPersonTypeToEventView(AddOrRemoveAllowedPersonTypeToEventView):
#     def _change_db(self, event):
#         event.allowed_person_types.add(self.person_type_obj)
#
#     def get_success_message(self, cleaned_data):
#         return f"Omezení pro typ členství {self.person_type_obj.get_person_type_display()} přidáno do události {self.object}"
#
#
# class RemoveAllowedPersonTypeFromEventView(AddOrRemoveAllowedPersonTypeToEventView):
#     def _change_db(self, event):
#         event.allowed_person_types.remove(self.person_type_obj)
#
#     def get_success_message(self, cleaned_data):
#         return f"Omezení pro typ členství {self.person_type_obj.get_person_type_display()} smazáno z události {self.object}"
