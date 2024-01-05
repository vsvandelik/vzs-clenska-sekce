from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.views.generic.list import ListView

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
    """
    Base mixin for views that operate on the :class:`Event` model.

    Also sets the ``context_object_name`` to ``event``.
    """

    context_object_name = "event"
    """:meta private:"""

    model = Event
    """:meta private:"""


class RedirectToEventDetailMixin:
    """
    Base mixin for views that redirect to the detail view of an event.

    The primary key of the event to which the view redirects
    is determined by the following order:

    1.  ``event_id`` URL keyword argument, if present
    2.  ``occurrence_id`` URL keyword argument, if present
    3.  ``object`` attribute of the view, if it is an instance of an event
    4.  ``event`` attribute of the ``object`` attribute of the view,
        if it is an instance of an event

    If none of the above applies, :class:`NotImplementedError` is raised.
    """

    def _get_event_id(self):
        """:meta private:"""

        kwargs = self.kwargs

        event_id = kwargs.get("event_id")
        if event_id is not None:
            return event_id

        occurrence_id = kwargs.get("occurrence_id")
        if occurrence_id is not None:
            return EventOccurrence.objects.get(pk=occurrence_id).event.id

        instance = getattr(self, "object", None)
        if instance is None:
            raise NotImplementedError

        if type(instance) is OneTimeEvent or type(instance) is Training:
            return instance.id

        related_event = getattr(instance, "event", None)
        if related_event is not None and (
            type(related_event) is OneTimeEvent or type(related_event) is Training
        ):
            return related_event.id

        raise NotImplementedError

    def reverse_redirect_url(self) -> str:
        """
        Returns the URL to redirect to.
        """

        id = self._get_event_id()

        event = Event.objects.get(pk=id)

        if isinstance(event, OneTimeEvent):
            viewname = "one_time_events:detail"
        elif isinstance(event, Training):
            viewname = "trainings:detail"
        else:
            raise NotImplementedError

        return reverse(viewname, kwargs={"pk": id})


class RedirectToEventDetailOnSuccessMixin(RedirectToEventDetailMixin):
    """
    Redirects to the detail view of an event on successful form submission.

    The logic is determined by :class:`RedirectToEventDetailMixin`.
    """

    def get_success_url(self):
        """:meta private:"""

        return self.reverse_redirect_url()


class RedirectToEventDetailOnFailureMixin(RedirectToEventDetailMixin):
    """
    Redirects to the detail view of an event on failed form submission.

    The logic is determined by :class:`RedirectToEventDetailMixin`.
    """

    def form_invalid(self, form):
        """:meta private:"""

        super().form_invalid(form)
        return HttpResponseRedirect(self.reverse_redirect_url())


class RedirectToOccurrenceFallbackEventDetailMixin:
    """
    Base mixin for views that redirect to the detail view of an occurrence.

    If the user cannot manage the occurrence's event,
    the view redirects to the detail view of the event instead.

    The primary key of the occurrence is determined by the following order:

    1.  ``occurrence_id`` URL keyword argument, if present
    2.  ``object`` attribute of the view, if it is an instance of an occurrence

    If none of the above applies, :class:`NotImplementedError` is raised.
    """

    def _get_occurrence_id(self):
        """:meta private:"""

        kwargs = self.kwargs

        occurrence_id = kwargs.get("occurrence_id")
        if occurrence_id is not None:
            return EventOccurrence.objects.get(pk=occurrence_id).id

        instance = getattr(self, "object", None)
        if instance is not None and (
            type(instance) is OneTimeEventOccurrence
            or type(instance) is TrainingOccurrence
        ):
            return instance.id

        raise NotImplementedError

    def reverse_redirect_url(self) -> str:
        """
        Returns the URL to redirect to.
        """

        id = self._get_occurrence_id()

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
            return reverse(viewname, kwargs={"event_id": event.id, "pk": id})
        else:
            if isinstance(event, OneTimeEvent):
                viewname = "one_time_events:detail"
            elif isinstance(event, Training):
                viewname = "trainings:detail"
            else:
                raise NotImplementedError
            return reverse(viewname, kwargs={"pk": event.id})


class RedirectToOccurrenceFallbackEventDetailOnSuccessMixin(
    RedirectToOccurrenceFallbackEventDetailMixin
):
    """
    Redirects to the detail view of an r
    or an event on successful form submission.

    The logic is determined by :class:`RedirectToOccurrenceFallbackEventDetailMixin`.
    """

    def get_success_url(self):
        """:meta private:"""

        return self.reverse_redirect_url()


class RedirectToOccurrenceFallbackEventDetailOnFailureMixin(
    RedirectToOccurrenceFallbackEventDetailMixin
):
    """
    Redirects to the detail view of an occurrence
    or an event on failed form submission.

    The logic is determined by :class:`RedirectToOccurrenceFallbackEventDetailMixin`.
    """

    def form_invalid(self, form):
        """:meta private:"""

        super().form_invalid(form)
        return HttpResponseRedirect(self.reverse_redirect_url())


class InsertEventIntoSelfObjectMixin:
    """
    Base mixin for views that handle events
    whose primary key is passed as ``event_id`` path parameter.

    Sets ``self.event`` to the :class:`Event` instance.
    """

    event_id_key = "event_id"
    """:meta private:"""

    def dispatch(self, request, *args, **kwargs):
        """:meta private:"""

        self.event = get_object_or_404(Event, pk=self.kwargs[self.event_id_key])
        return super().dispatch(request, *args, **kwargs)


class InsertOccurrenceIntoSelfObjectMixin:
    """
    Base mixin for views that handle event occurrences
    whose primary key is passed as ``occurrence_id`` path parameter.

    Sets ``self.occurrence`` to the :class:`EventOccurrence` instance.
    """

    occurrence_id_key = "occurrence_id"
    """:meta private:"""

    def dispatch(self, request, *args, **kwargs):
        """:meta private:"""

        self.occurrence = get_object_or_404(
            EventOccurrence, pk=self.kwargs[self.occurrence_id_key]
        )
        return super().dispatch(request, *args, **kwargs)


class InsertEventIntoModelFormKwargsMixin(InsertEventIntoSelfObjectMixin):
    """
    Base mixin for views that process events in their forms.

    Passes ``event`` as a keyword argument to the form.

    The event comes from :class:`InsertEventIntoSelfObjectMixin`.
    """

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.event
        return kwargs


class InsertOccurrenceIntoModelFormKwargsMixin(InsertOccurrenceIntoSelfObjectMixin):
    """
    Base mixin for views that process event occurrences in their forms.

    Passes ``occurrence`` as a keyword argument to the form.

    The occurrence comes from :class:`InsertOccurrenceIntoSelfObjectMixin`.
    """

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs["occurrence"] = self.occurrence
        return kwargs


class InsertEventIntoContextData(InsertEventIntoSelfObjectMixin):
    """
    Base mixin for views that process events in their templates.

    The event comes from :class:`InsertEventIntoSelfObjectMixin`.
    """

    def get_context_data(self, **kwargs):
        """
        *   ``event`` - the event instance
        """

        kwargs.setdefault("event", self.event)
        return super().get_context_data(**kwargs)


class InsertOccurrenceIntoContextData(InsertOccurrenceIntoSelfObjectMixin):
    """
    Base mixin for views that process event occurrences in their templates.

    The occurrence comes from :class:`InsertOccurrenceIntoSelfObjectMixin`.
    """

    def get_context_data(self, **kwargs):
        """
        *   ``occurrence`` - the occurrence instance
        *   ``event`` - the occurrence's event
        """

        kwargs.setdefault("occurrence", self.occurrence)
        kwargs.setdefault("event", self.occurrence.event)
        return super().get_context_data(**kwargs)


class InsertPositionAssignmentIntoSelfObject:
    """
    Base mixin for views that handle position assignments
    whose primary key is passed as ``position_assignment_id`` path parameter.

    Sets ``self.position_assignment`` to the :class:`EventPositionAssignment` instance.
    """

    position_assignment_id_key = "position_assignment_id"
    """:meta private:"""

    def dispatch(self, request, *args, **kwargs):
        """:meta private:"""

        self.position_assignment = get_object_or_404(
            EventPositionAssignment, pk=self.kwargs[self.position_assignment_id_key]
        )
        return super().dispatch(request, *args, **kwargs)


class InsertPositionAssignmentIntoModelFormKwargs(
    InsertPositionAssignmentIntoSelfObject
):
    """
    Base mixin for views that process position assignments in their forms.

    Passes ``position_assignment`` as a keyword argument to the form.

    The assignment comes from :class:`InsertPositionAssignmentIntoSelfObject`.
    """

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs["position_assignment"] = self.position_assignment
        return kwargs


class EventRestrictionMixin(RedirectToEventDetailOnSuccessMixin):
    """:meta private:"""

    model = Event
    """:meta private:"""


class EventCreateUpdateMixin(
    EventMixin, RedirectToEventDetailOnSuccessMixin, MessagesMixin, FormView
):
    """:meta private:"""

    pass


class EventCreateMixin(EventCreatePermissionMixin, EventCreateUpdateMixin, CreateView):
    """:meta private:"""

    success_message = "Událost %(name)s úspěšně přidána."
    """:meta private:"""


class EventUpdateMixin(EventManagePermissionMixin, EventCreateUpdateMixin, UpdateView):
    """:meta private:"""

    success_message = "Událost %(name)s úspěšně upravena."
    """:meta private:"""


class EventGeneratesDatesMixin:
    """
    Populates the ``dates`` context variable with event dates info.
    """

    def get_context_data(self, **kwargs):
        """
        *   ``dates`` - the event dates info
        """

        kwargs.setdefault("dates", self.get_form().generate_dates())
        return super().get_context_data(**kwargs)


class PersonTypeInsertIntoContextDataMixin:
    """
    Populates the ``available_person_types`` with all valid person types
    and the ``person_types_required`` with the person types allowed by the event.
    """

    def get_context_data(self, **kwargs):
        """:meta private:"""

        kwargs.setdefault("available_person_types", Person.Type.valid_choices())
        kwargs.setdefault(
            "person_types_required",
            self.object.allowed_person_types.values_list("person_type", flat=True),
        )
        return super().get_context_data(**kwargs)


class EventDetailMixin(
    EventInteractPermissionMixin,
    EventMixin,
    PersonTypeInsertIntoContextDataMixin,
    DetailView,
):
    """
    Mixin for event detail views.

    Sets the appropriate context variables.
    """

    def get_context_data(self, **kwargs):
        """
        *   ``active_person_can_enroll`` - whether the active person can enroll
        *   ``active_person_can_enroll_as_waiting`` - whether the active person
            can enroll as waiting
        *   ``active_person_can_unenroll`` - whether the active person can unenroll
        *   ``active_person_enrollment`` - the active person's enrollment instance
        """

        active_person = self.request.active_person
        event = self.object

        kwargs.setdefault(
            "active_person_can_enroll",
            event.can_person_enroll_as_participant(active_person),
        )
        kwargs.setdefault(
            "active_person_can_enroll_as_waiting",
            event.can_person_enroll_as_waiting(active_person),
        )
        kwargs.setdefault(
            "active_person_can_unenroll",
            event.can_participant_unenroll(active_person),
        )
        kwargs.setdefault(
            "active_person_enrollment",
            event.get_participant_enrollment(active_person),
        )

        return super().get_context_data(**kwargs)


class EventAdminListMixin(PermissionRequiredMixin, ListView):
    """
    Mixin for admin event list views.

    Uses ``self.filter_form`` to filter the events. Set in child classes.
    """

    permissions_formula = [[]]  # TODO: permissions
    """:meta private:"""

    def __init__(self, **kwargs):
        """:meta private:"""

        super().__init__(**kwargs)
        self.filter_form = None

    def get_context_data(self, **kwargs):
        """
        *   ``form`` - ``self.filter_form``
        *   ``filtered_get`` - url encoded GET parameters
        """

        kwargs.setdefault("form", self.filter_form)
        kwargs.setdefault("filtered_get", self.request.GET.urlencode())

        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """
        Filters and orders the events return by :meth:`get_accessible_events` by name.
        """

        events = self.get_accessible_events()

        return self.filter_form.process_filter(events).order_by("name")

    def get_accessible_events(self):
        """
        Override for a custom events queryset.
        """

        return Event.objects.all()


class EventDeleteView(
    EventManagePermissionMixin, EventMixin, MessagesMixin, DeleteView
):
    """
    Deletes an event.

    **Success redirection view**:
    If the request comes from the index or admin list view, redirects to it.
    Otherwise redirects to the admin list view for superusers
    and to the index view for all others.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``pk`` - event ID
    """

    template_name = "events/modals/delete.html"
    """:meta private:"""

    def get_success_url(self):
        """:meta private:"""

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
        """:meta private:"""

        return f"Událost {self.object.name} úspěšně smazána"


class EventPositionAssignmentMixin(
    EventManagePermissionMixin, MessagesMixin, RedirectToEventDetailOnSuccessMixin
):
    """
    Mixin for views that handle event position assignments.
    """

    context_object_name = "position_assignment"
    event_id_key = "event_id"
    model = EventPositionAssignment


class EventPositionAssignmentCreateUpdateMixin(EventPositionAssignmentMixin):
    """
    Mixin for views that assign or remove positions from events.
    """

    form_class = EventPositionAssignmentForm
    """:meta private:"""


class EventPositionAssignmentCreateView(
    InsertEventIntoModelFormKwargsMixin,
    EventPositionAssignmentCreateUpdateMixin,
    CreateView,
):
    """
    Assigns a position to an event.

    **Success redirection view**: The detail view of the event
    the position was assigned to.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID

    **Request body parameters:**

    *   ``position`` - the assigned position ID
    *   ``count`` - free capacity for that position at the event
    """

    success_message = "Organizátorská pozice %(position)s přidána"
    """:meta private:"""

    template_name = "events/create_event_position_assignment.html"
    """:meta private:"""


class EventPositionAssignmentUpdateView(
    EventPositionAssignmentCreateUpdateMixin, UpdateView
):
    """
    Updates event position assignment.

    **Success redirection view**: The detail view of the event
    the position is assigned to.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID
    *   ``pk`` - position assignment ID

    **Request body parameters:**

    *   ``position`` - the assigned position ID
    *   ``count`` - free capacity for that position at the event
    """

    success_message = "Organizátorská pozice %(position)s upravena"
    """:meta private:"""

    template_name = "events/edit_event_position_assignment.html"
    """:meta private:"""

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.object.event
        kwargs["position"] = self.object.position
        return kwargs


class EventPositionAssignmentDeleteView(EventPositionAssignmentMixin, DeleteView):
    """
    Deletes an event position assignment.

    **Success redirection view**: The detail view of the event
    the position was assigned to.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``event_id`` - event ID
    *   ``pk`` - position assignment ID
    """

    template_name = "events/modals/delete_event_position_assignment.html"
    """:meta private:"""

    def get_success_message(self, cleaned_data):
        """:meta private:"""

        return f"Organizátorská pozice {self.object.position} smazána"


class EditAgeLimitView(
    EventManagePermissionMixin, MessagesMixin, EventRestrictionMixin, UpdateView
):
    """
    Edits the age limit for an event.

    **Success redirection view**: The detail view of the edited event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``pk`` - event ID

    **Request body parameters:**

    *   ``min_age`` - minimum age
    *   ``max_age`` - maximum age
    """

    form_class = EventAgeLimitForm
    """:meta private:"""

    success_message = "Změna věkového omezení uložena"
    """:meta private:"""

    template_name = "events/edit_age_limit.html"
    """:meta private:"""


class EditGroupMembershipView(
    EventManagePermissionMixin, MessagesMixin, EventRestrictionMixin, UpdateView
):
    """
    Edits the group membership requirement for an event.

    **Success redirection view**: The detail view of the edited event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``pk`` - event ID

    **Request body parameters:**

    *   ``group`` - group to which the person must belong
    """

    form_class = EventGroupMembershipForm
    """:meta private:"""

    success_message = "Změna vyžadování skupiny uložena"
    """:meta private:"""

    template_name = "events/edit_group_membership.html"
    """:meta private:"""


class AddRemoveAllowedPersonTypeView(
    EventManagePermissionMixin,
    InsertEventIntoSelfObjectMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    UpdateView,
):
    """
    Flips the requirement of a person type for an event.

    **Success redirection view**: The detail view of the edited event.

    **Permissions**:

    Users that manage the event.

    **Path parameters:**

    *   ``pk`` - event ID

    **Request body parameters:**

    *   ``person_type`` - the person type to flip the requirement of
    """

    event_id_key = "pk"
    """:meta private:"""

    form_class = EventAllowedPersonTypeForm
    """:meta private:"""

    model = Event
    """:meta private:"""

    success_message = "Změna omezení na typ členství uložena"
    """:meta private:"""

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.event
        return kwargs


class ParticipantEnrollmentMixin(RedirectToEventDetailOnSuccessMixin, MessagesMixin):
    """:meta private:"""

    context_object_name = "enrollment"
    """:meta private:"""


class ParticipantEnrollmentCreateMixin(
    EventManagePermissionMixin,
    ParticipantEnrollmentMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
    CreateView,
):
    """
    Mixin for views that enroll participants into events.
    """

    success_message = "Přihlášení nového účastníka proběhlo úspěšně"
    """:meta private:"""


class ParticipantEnrollmentUpdateMixin(
    ParticipantEnrollmentMixin,
    UpdateView,
):
    """
    Mixin for views that edit event participant enrollments.
    """

    success_message = "Změna přihlášky proběhla úspěšně"
    """:meta private:"""

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.object.event
        kwargs["person"] = self.object.person
        return kwargs

    def get_context_data(self, **kwargs):
        """:meta private:"""

        kwargs.setdefault("event", self.object.event)
        return super().get_context_data(**kwargs)


class ParticipantEnrollmentDeleteMixin(
    EventManagePermissionMixin, ParticipantEnrollmentMixin, DeleteView
):
    """
    Mixin for views that unenroll participants from events.
    """

    event_id_key = "event_id"
    """:meta private:"""

    model = ParticipantEnrollment
    """:meta private:"""

    def get_success_message(self, cleaned_data):
        """:meta private:"""

        return f"Přihláška osoby {self.object.person} smazána"


class EnrollMyselfParticipantMixin(
    EventInteractPermissionMixin,
    InsertEventIntoModelFormKwargsMixin,
    InsertEventIntoContextData,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    InsertActivePersonIntoModelFormKwargsMixin,
    CreateView,
):
    """
    Mixin for views that enroll the active person into events.
    """

    pass


class UnenrollMyselfParticipantView(
    UnenrollMyselfPermissionMixin,
    MessagesMixin,
    RedirectToEventDetailOnSuccessMixin,
    RedirectToEventDetailOnFailureMixin,
    DeleteView,
):
    """
    Unenrolls the active person from an event.

    **Success redirection view**: The detail view of the event

    **Permissions**:

    Active users associated with the same person as the enrollment.

    **Path parameters:**

    *   ``pk`` - enrollment ID
    """

    context_object_name = "enrollment"
    """:meta private:"""

    model = ParticipantEnrollment
    """:meta private:"""

    success_message = "Odhlášení z události proběhlo úspěšně"
    """:meta private:"""

    template_name = "events/modals/unenroll_myself_participant.html"
    """:meta private:"""

    def form_valid(self, form):
        """:meta private:"""

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
    UpdateView,
):
    """:meta private:"""

    event_id_key = "pk"
    """:meta private:"""

    model = Event
    """:meta private:"""

    success_message = "Počet schválených přihlášek: %(count)s"
    """:meta private:"""

    def get_form_kwargs(self):
        """:meta private:"""

        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.event
        return kwargs


class OccurrenceProviderMixin:
    """
    Mixin for views that handle event occurences.

    Throws a 404 if the occurrence is not valid.
    """

    occurrence_q_condition_restriction = Q()
    """:meta private:"""

    def is_occurrence_valid(self, occurrence, kwargs) -> bool:
        """
        Abstract method that determines whether the occurrence is valid.
        """

        raise NotImplementedError

    def dispatch(self, request, *args, **kwargs):
        """:meta private:"""

        occurrence = self._get_occurrence(*args, **kwargs)

        if not self.is_occurrence_valid(occurrence, kwargs):
            raise Http404("Tato stránka není dostupná")

        return super().dispatch(request, *args, **kwargs)

    def _get_occurrence(self, *args, **kwargs):
        """:meta private:"""

        if "occurrence_id" in kwargs:
            pk = kwargs["occurrence_id"]
        elif "pk" in kwargs:
            pk = kwargs["pk"]
        else:
            raise NotImplementedError

        occurrence_set = EventOccurrence.objects.filter(
            Q(pk=pk) & self.occurrence_q_condition_restriction
        )

        return occurrence_set.first()


class OccurrenceRestrictionMixin(OccurrenceProviderMixin):
    """:meta private:"""

    def is_occurrence_valid(self, occurrence, kwargs):
        """:meta private:"""

        return occurrence is not None


class EventOccurrenceIdCheckMixin(OccurrenceProviderMixin):
    """:meta private:"""

    def is_occurrence_valid(self, occurrence, kwargs):
        """:meta private:"""

        return occurrence.event.id == kwargs["event_id"]


class OccurrenceDetailBaseView(
    OccurrenceDetailPermissionMixin,
    InsertEventIntoContextData,
    InsertOccurrenceIntoContextData,
    EventOccurrenceIdCheckMixin,
    DetailView,
):
    """
    Base view for event occurrence detail views.
    """

    occurrence_id_key = "pk"
    """:meta private:"""


class OccurrenceOpenRestrictionMixin(OccurrenceRestrictionMixin):
    """
    Restricts the view only to open occurrences. 404 otherwise.
    """

    occurrence_q_condition_restriction = Q(state=EventOrOccurrenceState.OPEN)
    """:meta private:"""


class OccurrenceNotOpenedRestrictionMixin(OccurrenceRestrictionMixin):
    """
    Restricts the view only to occurrences that are not open. 404 otherwise.
    """

    occurrence_q_condition_restriction = ~Q(state=EventOrOccurrenceState.OPEN)
    """:meta private:"""


class OccurrenceIsClosedRestrictionMixin(OccurrenceRestrictionMixin):
    """
    Restricts the view only to closed occurrences. 404 otherwise.
    """

    occurrence_q_condition_restriction = Q(state=EventOrOccurrenceState.CLOSED)
    """:meta private:"""


class OccurrenceIsApprovedRestrictionMixin(OccurrenceRestrictionMixin):
    """
    Restricts the view only to completed occurrences. 404 otherwise.
    """

    occurrence_q_condition_restriction = Q(state=EventOrOccurrenceState.COMPLETED)
    """:meta private:"""


class OccurrenceNotApprovedRestrictionMixin(OccurrenceRestrictionMixin):
    """
    Restricts the view only to occurrences that are not completed. 404 otherwise.
    """

    occurrence_q_condition_restriction = ~Q(state=EventOrOccurrenceState.COMPLETED)
    """:meta private:"""
