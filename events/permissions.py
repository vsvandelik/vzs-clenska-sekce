from users.views import PermissionRequiredMixin

from .models import (
    Event,
    EventOccurrence,
    EventPositionAssignment,
    OrganizerAssignment,
    ParticipantEnrollment,
)


class EventCreatePermissionMixin(PermissionRequiredMixin):
    @classmethod
    def view_has_permission_POST(cls, active_user, POST, **kwargs):
        return active_user.has_perm(POST["category"])

    @classmethod
    def view_has_permission(cls, method: str, active_user, **kwargs):
        if method == "POST":
            return cls.view_has_permission_POST(active_user, **kwargs)

        return super().view_has_permission(method, active_user, **kwargs)


class ObjectPermissionMixin(PermissionRequiredMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        raise NotImplementedError

    @classmethod
    def permission_predicate(cls, instance, active_user):
        raise NotImplementedError

    @classmethod
    def view_has_permission(cls, method:str, active_user, **kwargs):
        instances = {
            instance_name: model_class.objects.filter(
                pk=kwargs[path_parameter_name]
            ).first()
            for path_parameter_name, (
                model_class,
                instance_name,
            ) in cls.get_path_parameter_mapping().items()
        }

        return cls.permission_predicate(active_user=active_user, **instances)


class EventPermissionMixin(ObjectPermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        event_id_key_opt = getattr(cls, "event_id_key", None)

        event_id_key = event_id_key_opt if event_id_key_opt is not None else "pk"

        return {event_id_key: (Event, "event")}


class OccurrencePermissionMixin(ObjectPermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.event.can_user_manage(active_user)

    @classmethod
    def get_path_parameter_mapping(cls):
        return {"occurrence_id": (EventOccurrence, "occurrence")}


class OccurrenceManagePermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_user_manage(active_user)


class OccurrenceManagePermissionMixin2(OccurrenceManagePermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        return {"pk": (EventOccurrence, "occurrence")}


class EventManagePermissionMixin(EventPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, active_user):
        return event.can_user_manage(active_user)


class EventInteractPermissionMixin(EventPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, active_user):
        return event.can_user_manage(active_user) or event.can_person_interact_with(
            active_user.person
        )


class UnenrollMyselfPermissionMixin(ObjectPermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        return {"pk": (ParticipantEnrollment, "enrollment")}

    @classmethod
    def permission_predicate(cls, enrollment, active_user):
        return enrollment.person == active_user.person


class OccurrenceEnrollOrganizerPermissionMixin(ObjectPermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        return {
            "occurrence_id": (EventOccurrence, "occurrence"),
            "position_assignment_id": (EventPositionAssignment, "position_assignment"),
        }

    @classmethod
    def permission_predicate(cls, occurrence, position_assignment, active_user):
        return occurrence.can_enroll_position(active_user.person, position_assignment)


class OccurrenceUnenrollOrganizerPermissionMixin(ObjectPermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        return {
            "occurrence_id": (EventOccurrence, "occurrence"),
            "pk": (OrganizerAssignment, "organizer_assignment"),
        }

    @classmethod
    def permission_predicate(cls, occurrence, organizer_assignment, active_user):
        return occurrence.can_unenroll_position(
            active_user.person, organizer_assignment.position_assignment
        )
