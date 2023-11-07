from events.models import (
    Event,
    EventOccurrence,
    EventPositionAssignment,
    OrganizerAssignment,
    ParticipantEnrollment,
)
from users.views import PermissionRequiredMixin


class ObjectPermissionMixin(PermissionRequiredMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        raise NotImplementedError

    @classmethod
    def permission_predicate(cls, instance, logged_in_user, active_person):
        raise NotImplementedError

    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, **kwargs):
        instances = {
            instance_name: model_class.objects.filter(
                pk=kwargs[path_parameter_name]
            ).first()
            for path_parameter_name, (
                model_class,
                instance_name,
            ) in cls.get_path_parameter_mapping().items()
        }

        return cls.permission_predicate(
            logged_in_user=logged_in_user, active_person=active_person, **instances
        )


class EventPermissionMixin(ObjectPermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        event_id_key_opt = getattr(cls, "event_id_key", None)

        event_id_key = event_id_key_opt if event_id_key_opt is not None else "pk"

        return {event_id_key: (Event, "event")}


class OccurrencePermissionMixin(ObjectPermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        return {"occurrence_id": (EventOccurrence, "occurrence")}


class OccurrenceManagePermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_user_manage(logged_in_user)


class OccurrenceManagePermissionMixin2(OccurrenceManagePermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        return {"pk": (EventOccurrence, "occurrence")}


class EventManagePermissionMixin(EventPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, logged_in_user, active_person):
        return event.can_user_manage(logged_in_user)


class EventInteractPermissionMixin(EventPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, logged_in_user, active_person):
        return event.can_user_manage(logged_in_user) or event.can_person_interact_with(
            active_person
        )


class UnenrollMyselfPermissionMixin(ObjectPermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        return {"pk": (ParticipantEnrollment, "enrollment")}

    @classmethod
    def permission_predicate(cls, enrollment, logged_in_user, active_person):
        return enrollment.person == active_person


class OccurrenceEnrollOrganizerPermissionMixin(ObjectPermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        return {
            "occurrence_id": (EventOccurrence, "occurrence"),
            "position_assignment_id": (EventPositionAssignment, "position_assignment"),
        }

    @classmethod
    def permission_predicate(
        cls, occurrence, position_assignment, logged_in_user, active_person
    ):
        return occurrence.can_enroll_position(active_person, position_assignment)


class OccurrenceUnenrollOrganizerPermissionMixin(ObjectPermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        return {
            "occurrence_id": (EventOccurrence, "occurrence"),
            "pk": (OrganizerAssignment, "organizer_assignment"),
        }

    @classmethod
    def permission_predicate(
        cls, occurrence, organizer_assignment, logged_in_user, active_person
    ):
        return occurrence.can_unenroll_position(
            active_person, organizer_assignment.position_assignment
        )
