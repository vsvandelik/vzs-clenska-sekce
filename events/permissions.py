from events.models import Event, EventOccurrence, ParticipantEnrollment
from users.views import PermissionRequiredMixin


class EventInteractPermissionMixinBase(PermissionRequiredMixin):
    @classmethod
    def get_event_id_key(cls):
        event_id_key = getattr(cls, "event_id_key", None)

        return event_id_key if event_id_key is not None else "pk"

    @classmethod
    def _permission_predicate(cls, event, logged_in_user, active_person):
        raise NotImplementedError

    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, **kwargs):
        event_pk = kwargs[cls.get_event_id_key()]

        for event in Event.objects.filter(pk=event_pk):
            return cls._permission_predicate(event, logged_in_user, active_person)

        return False


class OccurrenceManagePermissionMixin(PermissionRequiredMixin):
    @classmethod
    def view_has_permission(
        cls, logged_in_user, active_person, occurrence_id, **kwargs
    ):
        for occurrence in EventOccurrence.objects.filter(pk=occurrence_id):
            return occurrence.event.can_user_manage(logged_in_user)

        return False


class EventManagePermissionMixin(EventInteractPermissionMixinBase):
    @classmethod
    def _permission_predicate(cls, event, logged_in_user, active_person):
        return event.can_user_manage(logged_in_user)


class EventInteractPermissionMixin(EventInteractPermissionMixinBase):
    @classmethod
    def _permission_predicate(cls, event, logged_in_user, active_person):
        return event.can_user_manage(logged_in_user) or event.can_person_interact_with(
            active_person
        )


class UnenrollMyselfPermissionMixin(PermissionRequiredMixin):
    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, pk):
        enrollment_pk = pk

        for enrollment in ParticipantEnrollment.objects.filter(pk=enrollment_pk):
            return enrollment.person == active_person

        return False
