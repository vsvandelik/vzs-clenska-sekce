from events.models import Event, EventOccurrence, ParticipantEnrollment
from users.views import PermissionRequiredMixin


class ObjectPermissionMixin(PermissionRequiredMixin):
    @classmethod
    def get_primary_key_name(cls):
        return "pk"

    @classmethod
    def get_model_class(cls):
        raise NotImplementedError

    @classmethod
    def predicate(cls, instance, logged_in_user, active_person):
        raise NotImplementedError

    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, **kwargs):
        pk = kwargs[cls.get_primary_key_name()]

        for instance in cls.get_model_class().objects.filter(pk=pk):
            return cls.predicate(instance, logged_in_user, active_person)

        return False


class EventPermissionMixin(ObjectPermissionMixin):
    @classmethod
    def get_primary_key_name(cls):
        event_id_key = getattr(cls, "event_id_key", None)

        return event_id_key if event_id_key is not None else "pk"

    @classmethod
    def get_model_class(cls):
        return Event


class OccurrencePermissionMixin(ObjectPermissionMixin):
    @classmethod
    def get_primary_key_name(cls):
        return "occurrence_id"

    @classmethod
    def get_model_class(cls):
        return EventOccurrence


class OccurrenceManagePermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.event.can_user_manage(logged_in_user)


class EventManagePermissionMixin(EventPermissionMixin):
    @classmethod
    def predicate(cls, event, logged_in_user, active_person):
        return event.can_user_manage(logged_in_user)


class EventInteractPermissionMixin(EventPermissionMixin):
    @classmethod
    def predicate(cls, event, logged_in_user, active_person):
        return event.can_user_manage(logged_in_user) or event.can_person_interact_with(
            active_person
        )


class UnenrollMyselfPermissionMixin(ObjectPermissionMixin):
    @classmethod
    def predicate(cls, enrollment, logged_in_user, active_person):
        return enrollment.person == active_person
