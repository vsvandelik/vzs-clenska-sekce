from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from events.models import EventOrOccurrenceState, ParticipantEnrollment
from one_time_events.models import OneTimeEvent, OneTimeEventOccurrence
from one_time_events.permissions import OccurrenceDetailPermissionMixin
from persons.models import Person, get_active_user
from trainings.models import Training, TrainingOccurrence
from users.permissions import PermissionRequiredMixin
from vzs.mixin_extensions import (
    InsertActivePersonIntoModelFormKwargsMixin,
    MessagesMixin,
)
from vzs.utils import send_notification_email
from .forms import (
    EventAgeLimitForm,
    EventAllowedPersonTypeForm,
    EventGroupMembershipForm,
    EventPositionAssignmentForm,
)
from .models import Event, EventOccurrence, EventPositionAssignment
from .permissions import (
    EventCreatePermissionMixin,
    EventInteractPermissionMixin,
    EventManagePermissionMixin,
    UnenrollMyselfPermissionMixin,
)


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


class RedirectToOccurrenceFallbackEventDetailMixin:
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
        event = occurrence.event
        active_user = get_active_user(self.request.active_person)
        if event.can_user_manage(active_user):
            if isinstance(occurrence, OneTimeEventOccurrence):
                viewname = "one_time_events:occurrence-detail"
            elif isinstance(occurrence, TrainingOccurrence):
                viewname = "trainings:occurrence-detail"
            else:
                raise NotImplementedError
            return viewname, event.id, id
        else:
            if isinstance(event, OneTimeEvent):
                viewname = "one_time_events:detail"
            elif isinstance(event, Training):
                viewname = "trainings:detail"
            else:
                raise NotImplementedError
            return viewname, event.id


class RedirectToOccurrenceFallbackEventDetailOnSuccessMixin(
    RedirectToOccurrenceFallbackEventDetailMixin
):
    def get_success_url(self):
        viewname, *params = super().get_redirect_viewname_id()
        return reverse(viewname, args=params)


class RedirectToOccurrenceFallbackEventDetailOnFailureMixin(
    RedirectToOccurrenceFallbackEventDetailMixin
):
    def form_invalid(self, form):
        super().form_invalid(form)
        viewname, *params = super().get_redirect_viewname_id()
        return HttpResponseRedirect(reverse(viewname, args=params))


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


class EventCreateMixin(
    EventCreatePermissionMixin, EventCreateUpdateMixin, generic.CreateView
):
    success_message = "Událost %(name)s úspěšně přidána."


class EventUpdateMixin(
    EventManagePermissionMixin, EventCreateUpdateMixin, generic.UpdateView
):
    success_message = "Událost %(name)s úspěšně upravena."


class EventGeneratesDatesMixin:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("dates", self.get_form().generate_dates())
        return super().get_context_data(**kwargs)


class PersonTypeInsertIntoContextDataMixin:
    def get_context_data(self, **kwargs):
        kwargs.setdefault("available_person_types", Person.Type.valid_choices())
        kwargs.setdefault(
            "person_types_required",
            self.object.allowed_person_types.values_list("person_type", flat=True),
        )
        return super().get_context_data(**kwargs)


class EventDetailBaseView(
    EventInteractPermissionMixin,
    EventMixin,
    PersonTypeInsertIntoContextDataMixin,
    generic.DetailView,
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


class EventAdminListMixin(PermissionRequiredMixin, generic.ListView):
    permissions_formula = [[]]  # TODO: permissions

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filter_form = None

    def get_context_data(self, **kwargs):
        kwargs.setdefault("form", self.filter_form)
        kwargs.setdefault("filtered_get", self.request.GET.urlencode())

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        events = self.get_accessible_events()

        return self.filter_form.process_filter(events).order_by("name")

    def get_accessible_events(self):
        return Event.objects.all()


class EventDeleteView(
    EventManagePermissionMixin, EventMixin, MessagesMixin, generic.DeleteView
):
    template_name = "events/modals/delete.html"

    def get_success_url(self):
        one_time_events_index = reverse("one_time_events:index")
        trainings_index = reverse("trainings:index")
        admin_one_time_events_index = reverse("one_time_events:list-admin")
        admin_trainings_index = reverse("trainings:list-admin")
        coming_from_uri = self.request.META["HTTP_REFERER"]
        if coming_from_uri not in [
            one_time_events_index,
            trainings_index,
            admin_one_time_events_index,
            admin_trainings_index,
        ]:
            active_user = get_active_user(self.request.active_person)
            if self.object.is_one_time_event():
                if active_user.has_perm("one_time_events:list-admin"):
                    return admin_one_time_events_index
                return one_time_events_index
            else:
                if active_user.has_perm("trainings:list-admin"):
                    return admin_trainings_index
                return trainings_index
        return coming_from_uri

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
    EventManagePermissionMixin,
    InsertEventIntoSelfObjectMixin,
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
    EventManagePermissionMixin,
    ParticipantEnrollmentMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
    generic.CreateView,
):
    success_message = "Přihlášení nového účastníka proběhlo úspěšně"


class ParticipantEnrollmentUpdateMixin(
    ParticipantEnrollmentMixin,
    generic.UpdateView,
):
    success_message = "Změna přihlášky proběhla úspěšně"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.object.event
        kwargs["person"] = self.object.person
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs.setdefault("event", self.object.event)
        return super().get_context_data(**kwargs)


class ParticipantEnrollmentDeleteMixin(
    EventManagePermissionMixin, ParticipantEnrollmentMixin, generic.DeleteView
):
    model = ParticipantEnrollment
    event_id_key = "event_id"

    def get_success_message(self, cleaned_data):
        return f"Přihláška osoby {self.object.person} smazána"


class EnrollMyselfParticipantMixin(
    EventInteractPermissionMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
    generic.CreateView,
):
    pass


class UnenrollMyselfParticipantView(
    UnenrollMyselfPermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    RedirectToEventDetailOnFailureMixin,
    generic.DeleteView,
):
    model = ParticipantEnrollment
    context_object_name = "enrollment"
    success_message = "Odhlášení z události proběhlo úspěšně"
    template_name = "events/modals/unenroll_myself_participant.html"

    def form_valid(self, form):
        enrollment = self.object
        send_notification_email(
            _("Odhlášení z události"),
            _(
                f"Byl(a) jste úspěšně odhlášen(a) z události {enrollment.event} na vlastní žádost"
            ),
            [enrollment.person],
        )
        return super().form_valid(form)


class BulkApproveParticipantsMixin(
    EventManagePermissionMixin,
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
    occurrence_q_condition_restriction = Q()

    def get_occurrence(self, *args, **kwargs):
        if "occurrence_id" in kwargs:
            pk = kwargs["occurrence_id"]
        elif "pk" in kwargs:
            pk = kwargs["pk"]
        else:
            raise NotImplementedError
        occurrence_set = EventOccurrence.objects.filter(
            Q(pk=pk) & self.occurrence_q_condition_restriction
        )
        if occurrence_set.exists():
            return occurrence_set.first()
        return None


class OccurrenceRestrictionMixin(GetOccurrenceProvider):
    def dispatch(self, request, *args, **kwargs):
        occurrence = super().get_occurrence(*args, **kwargs)
        if occurrence is None:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class EventOccurrenceIdCheckMixin(GetOccurrenceProvider):
    def dispatch(self, request, *args, **kwargs):
        occurrence = super().get_occurrence(*args, **kwargs)
        if occurrence.event.id != kwargs["event_id"]:
            raise Http404("Tato stránka není dostupná")
        return super().dispatch(request, *args, **kwargs)


class OccurrenceDetailBaseView(
    OccurrenceDetailPermissionMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    EventOccurrenceIdCheckMixin,
    generic.DetailView,
):
    occurrence_id_key = "pk"


class OccurrenceOpenRestrictionMixin(OccurrenceRestrictionMixin):
    occurrence_q_condition_restriction = Q(state=EventOrOccurrenceState.OPEN)


class OccurrenceNotOpenedRestrictionMixin(OccurrenceRestrictionMixin):
    occurrence_q_condition_restriction = ~Q(state=EventOrOccurrenceState.OPEN)


class OccurrenceIsClosedRestrictionMixin(OccurrenceRestrictionMixin):
    occurrence_q_condition_restriction = Q(state=EventOrOccurrenceState.CLOSED)


class OccurrenceIsApprovedRestrictionMixin(OccurrenceRestrictionMixin):
    occurrence_q_condition_restriction = Q(state=EventOrOccurrenceState.COMPLETED)


class OccurrenceNotApprovedRestrictionMixin(OccurrenceRestrictionMixin):
    occurrence_q_condition_restriction = ~Q(state=EventOrOccurrenceState.COMPLETED)
