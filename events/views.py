from datetime import datetime
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from events.models import ParticipantEnrollment, EventOrOccurrenceState
from one_time_events.models import OneTimeEvent, OneTimeEventOccurrence
from persons.models import Person
from trainings.models import Training, TrainingOccurrence
from users.views import PermissionRequiredMixin
from vzs.mixin_extensions import (
    InsertActivePersonIntoModelFormKwargsMixin,
    MessagesMixin,
)

from .forms import (
    EventAgeLimitForm,
    EventAllowedPersonTypeForm,
    EventGroupMembershipForm,
    EventPositionAssignmentForm,
)
from .models import Event, EventOccurrence, EventPositionAssignment


class EventManagePermissionMixin(PermissionRequiredMixin):
    event_id_key = "pk"

    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, **kwargs):
        event_pk = kwargs[cls.event_id_key]

        for event in Event.objects.filter(pk=event_pk):
            return event.can_user_manage(logged_in_user)


class EventMixin:
    model = Event
    context_object_name = "event"


class RedirectToEventDetailMixin:
    def get_redirect_viewname_id(self):
        if "event_id" in self.kwargs:
            id = self.kwargs["event_id"]
        elif "occurrence_id" in self.kwargs:
            id = EventOccurrence.objects.get(pk=self.kwargs["occurrence_id"]).event.id
        elif hasattr(self, "object"):
            if type(self.object) is OneTimeEvent or type(self.object) is Training:
                id = self.object.id
            elif hasattr(self.object, "event") and (
                type(self.object.event) is OneTimeEvent
                or type(self.object.event) is Training
            ):
                id = self.object.event.id
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError

        event = Event.objects.get(pk=id)
        if isinstance(event, OneTimeEvent):
            viewname = "one_time_events:detail"
        elif isinstance(event, Training):
            viewname = "trainings:detail"
        else:
            raise NotImplementedError
        return viewname, id


class RedirectToEventDetailOnSuccessMixin(RedirectToEventDetailMixin):
    def get_success_url(self):
        viewname, id = super().get_redirect_viewname_id()
        return reverse(viewname, args=[id])


class RedirectToEventDetailOnFailureMixin(RedirectToEventDetailMixin):
    def form_invalid(self, form):
        super().form_invalid(form)
        viewname, id = super().get_redirect_viewname_id()
        return redirect(viewname, pk=id)


class RedirectToOccurrenceDetailMixin:
    def get_redirect_viewname_id(self):
        if "occurrence_id" in self.kwargs:
            id = EventOccurrence.objects.get(pk=self.kwargs["occurrence_id"]).id
        elif hasattr(self, "object") and (
            type(self.object) is OneTimeEventOccurrence
            or type(self.object) is TrainingOccurrence
        ):
            id = self.object.id
        else:
            raise NotImplementedError

        occurrence = EventOccurrence.objects.get(pk=id)
        if isinstance(occurrence, OneTimeEventOccurrence):
            viewname = "one_time_events:occurrence-detail"
        elif isinstance(occurrence, TrainingOccurrence):
            viewname = "trainings:occurrence-detail"
        else:
            raise NotImplementedError
        return viewname, occurrence.event.id, id


class RedirectToOccurrenceDetailOnSuccessMixin(RedirectToOccurrenceDetailMixin):
    def get_success_url(self):
        viewname, event_id, occurrence_id = super().get_redirect_viewname_id()
        return reverse(viewname, args=[event_id, occurrence_id])


class RedirectToOccurrenceDetailOnFailureMixin(RedirectToOccurrenceDetailMixin):
    def form_invalid(self, form):
        super().form_invalid(form)
        viewname, event_id, occurrence_id = super().get_redirect_viewname_id()
        return redirect(viewname, event_id=event_id, pk=occurrence_id)


class InsertEventIntoSelfObjectMixin:
    event_id_key = "event_id"

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=self.kwargs[self.event_id_key])
        return super().dispatch(request, *args, **kwargs)


class InsertOccurrenceIntoSelfObjectMixin:
    occurrence_id_key = "occurrence_id"

    def dispatch(self, request, *args, **kwargs):
        self.occurrence = get_object_or_404(
            EventOccurrence, pk=self.kwargs[self.occurrence_id_key]
        )
        return super().dispatch(request, *args, **kwargs)


class InsertEventIntoModelFormKwargsMixin(InsertEventIntoSelfObjectMixin):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.event
        return kwargs


class InsertOccurrenceIntoModelFormKwargsMixin(InsertOccurrenceIntoSelfObjectMixin):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["occurrence"] = self.occurrence
        return kwargs


class InsertEventIntoContextData(InsertEventIntoSelfObjectMixin):
    def get_context_data(self, **kwargs):
        kwargs.setdefault("event", self.event)
        return super().get_context_data(**kwargs)


class InsertOccurrenceIntoContextData(InsertOccurrenceIntoSelfObjectMixin):
    def get_context_data(self, **kwargs):
        kwargs.setdefault("occurrence", self.occurrence)
        kwargs.setdefault("event", self.occurrence.event)
        return super().get_context_data(**kwargs)


class InsertPositionAssignmentIntoSelfObject:
    position_assignment_id_key = "position_assignment_id"

    def dispatch(self, request, *args, **kwargs):
        self.position_assignment = get_object_or_404(
            EventPositionAssignment, pk=self.kwargs[self.position_assignment_id_key]
        )
        return super().dispatch(request, *args, **kwargs)


class InsertPositionAssignmentIntoModelFormKwargs(
    InsertPositionAssignmentIntoSelfObject
):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["position_assignment"] = self.position_assignment
        return kwargs


class EventRestrictionMixin(RedirectToEventDetailOnSuccessMixin):
    model = Event


class EventCreateUpdateMixin(
    EventMixin, RedirectToEventDetailOnSuccessMixin, MessagesMixin, generic.FormView
):
    pass


class EventCreateMixin(EventCreateUpdateMixin, generic.CreateView):
    success_message = "Událost %(name)s úspěšně přidána."


class EventUpdateMixin(EventCreateUpdateMixin, generic.UpdateView):
    success_message = "Událost %(name)s úspěšně upravena."


class EventGeneratesDatesMixin:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("dates", self.get_form().generate_dates())
        return super().get_context_data(**kwargs)


class PersonTypeInsertIntoContextDataMixin:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("available_person_types", Person.Type.choices)
        kwargs.setdefault(
            "person_types_required",
            self.object.allowed_person_types.values_list("person_type", flat=True),
        )
        return super().get_context_data(**kwargs)


class EventDetailBaseView(
    EventMixin, PersonTypeInsertIntoContextDataMixin, generic.DetailView
):
    def get_context_data(self, **kwargs):
        active_person = self.request.active_person
        kwargs.setdefault(
            "active_person_can_enroll",
            self.object.can_person_enroll_as_participant(active_person),
        )
        kwargs.setdefault(
            "active_person_can_enroll_as_waiting",
            self.object.can_person_enroll_as_waiting(active_person),
        )
        kwargs.setdefault(
            "active_person_can_unenroll",
            self.object.can_participant_unenroll(active_person),
        )
        kwargs.setdefault(
            "active_person_enrollment",
            self.object.get_participant_enrollment(active_person),
        )
        return super().get_context_data(**kwargs)


class EventIndexView(LoginRequiredMixin, generic.ListView):
    template_name = "events/index.html"
    context_object_name = "events"

    def get_queryset(self):
        user = self.request.user
        active_person = self.request.active_person

        visible_event_pks = [
            event.pk
            for event in Event.objects.all()
            if event.can_user_manage(user)
            or event.can_person_interact_with(active_person)
        ]

        return Event.objects.filter(pk__in=visible_event_pks)


class EventDeleteView(
    EventManagePermissionMixin, EventMixin, MessagesMixin, generic.DeleteView
):
    template_name = "events/modals/delete.html"
    success_url = reverse_lazy("events:index")

    def get_success_message(self, cleaned_data):
        return f"Událost {self.object.name} úspěšně smazána"


class EventPositionAssignmentMixin(
    EventManagePermissionMixin, MessagesMixin, RedirectToEventDetailOnSuccessMixin
):
    model = EventPositionAssignment
    context_object_name = "position_assignment"
    event_id_key = "event_id"


class EventPositionAssignmentCreateUpdateMixin(EventPositionAssignmentMixin):
    form_class = EventPositionAssignmentForm


class EventPositionAssignmentCreateView(
    InsertEventIntoModelFormKwargsMixin,
    EventPositionAssignmentCreateUpdateMixin,
    generic.CreateView,
):
    template_name = "events/create_event_position_assignment.html"
    success_message = "Organizátorská pozice %(position)s přidána"


class EventPositionAssignmentUpdateView(
    EventPositionAssignmentCreateUpdateMixin, generic.UpdateView
):
    template_name = "events/edit_event_position_assignment.html"
    success_message = "Organizátorská pozice %(position)s upravena"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.object.event
        kwargs["position"] = self.object.position
        return kwargs


class EventPositionAssignmentDeleteView(
    EventPositionAssignmentMixin, generic.DeleteView
):
    template_name = "events/modals/delete_event_position_assignment.html"

    def get_success_message(self, cleaned_data):
        return f"Organizátorská pozice {self.object.position} smazána"


class EditAgeLimitView(
    EventManagePermissionMixin, MessagesMixin, EventRestrictionMixin, generic.UpdateView
):
    template_name = "events/edit_age_limit.html"
    form_class = EventAgeLimitForm
    success_message = "Změna věkového omezení uložena"


class EditGroupMembershipView(
    EventManagePermissionMixin, MessagesMixin, EventRestrictionMixin, generic.UpdateView
):
    template_name = "events/edit_group_membership.html"
    form_class = EventGroupMembershipForm
    success_message = "Změna vyžadování skupiny uložena"


class AddRemoveAllowedPersonTypeView(
    InsertEventIntoSelfObjectMixin,
    EventManagePermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    generic.UpdateView,
):
    event_id_key = "pk"
    form_class = EventAllowedPersonTypeForm
    success_message = "Změna omezení na typ členství uložena"
    model = Event

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.event
        return kwargs


class ParticipantEnrollmentMixin(RedirectToEventDetailOnSuccessMixin, MessagesMixin):
    context_object_name = "enrollment"


class ParticipantEnrollmentCreateMixin(
    ParticipantEnrollmentMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
    generic.CreateView,
):
    success_message = "Přihlášení nového účastníka proběhlo úspěšně"


class ParticipantEnrollmentUpdateMixin(ParticipantEnrollmentMixin, generic.UpdateView):
    success_message = "Změna přihlášky proběhla úspěšně"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.object.event
        kwargs["person"] = self.object.person
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs.setdefault("event", self.object.event)
        return super().get_context_data(**kwargs)


class ParticipantEnrollmentDeleteMixin(ParticipantEnrollmentMixin, generic.DeleteView):
    model = ParticipantEnrollment

    def get_success_message(self, cleaned_data):
        return f"Přihláška osoby {self.object.person} smazána"


class EnrollMyselfParticipantMixin(
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
    generic.CreateView,
):
    pass


class UnenrollMyselfParticipantView(
    PermissionRequiredMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    RedirectToEventDetailOnFailureMixin,
    generic.DeleteView,
):
    model = ParticipantEnrollment
    context_object_name = "enrollment"
    success_message = "Odhlášení z události proběhlo úspěšně"
    template_name = "events/modals/unenroll_myself_participant.html"

    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, pk):
        enrollment_pk = pk

        for enrollment in ParticipantEnrollment.objects.filter(pk=enrollment_pk):
            return enrollment.person == active_person

        return False


class BulkApproveParticipantsMixin(
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertEventIntoContextData,
    generic.UpdateView,
):
    event_id_key = "pk"
    success_message = "Počet schválených přihlášek: %(count)s"
    model = Event

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.event
        return kwargs


class GetOccurrenceProvider:
    def get_occurrence(self, *args, **kwargs):
        if "occurrence_id" in kwargs:
            pk = kwargs["occurrence_id"]
        elif "pk" in kwargs:
            pk = kwargs["pk"]
        else:
            raise NotImplementedError
        return get_object_or_404(EventOccurrence, pk=pk)


class EventOccurrenceIdCheckMixin(GetOccurrenceProvider):
    def dispatch(self, request, *args, **kwargs):
        occurrence = super().get_occurrence(*args, **kwargs)
        if occurrence.event.id != kwargs["event_id"]:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class OccurrenceDetailBaseView(
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    EventOccurrenceIdCheckMixin,
    generic.DetailView,
):
    occurrence_id_key = "pk"


class OccurrenceOpenRestrictionMixin(GetOccurrenceProvider):
    def dispatch(self, request, *args, **kwargs):
        occurrence = super().get_occurrence(*args, **kwargs)
        if occurrence.state != EventOrOccurrenceState.OPEN:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class OccurrenceNotOpenedRestrictionMixin(GetOccurrenceProvider):
    def dispatch(self, request, *args, **kwargs):
        occurrence = super().get_occurrence(*args, **kwargs)
        if occurrence.state == EventOrOccurrenceState.OPEN:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class OccurrenceIsClosedRestrictionMixin(GetOccurrenceProvider):
    def dispatch(self, request, *args, **kwargs):
        occurrence = super().get_occurrence(*args, **kwargs)
        if occurrence.state != EventOrOccurrenceState.CLOSED:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class OccurrenceIsApprovedRestrictionMixin(GetOccurrenceProvider):
    def dispatch(self, request, *args, **kwargs):
        occurrence = super().get_occurrence(*args, **kwargs)
        if occurrence.state != EventOrOccurrenceState.COMPLETED:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)
