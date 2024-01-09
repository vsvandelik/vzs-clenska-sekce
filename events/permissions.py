from users.permissions import LoginRequiredMixin
from users.views import PermissionRequiredMixin

from .models import (
    Event,
    EventOccurrence,
    EventPositionAssignment,
    OrganizerAssignment,
    ParticipantEnrollment,
)


class EventCreatePermissionMixin(PermissionRequiredMixin):
    """
    Permits only users that manage the event category sent in the POST request.

    Doesn't implement permission logic for GET requests,
    override for specifying that behavior.
    """

    @classmethod
    def view_has_permission(cls, method: str, active_user, POST, **kwargs):
        """:meta private:"""

        if method == "POST":
            return active_user.has_perm(POST["category"])

        return super().view_has_permission(method, active_user, POST=POST, **kwargs)


class ObjectPermissionMixin(LoginRequiredMixin):
    """
    Base class for permission mixins that work with model instances whose primary key
    is passed as a path parameter.
    """

    @classmethod
    def get_path_parameter_mapping(cls):
        """
        Abstract method.

        Returns a mapping from path parameter names to
        pairs of model classes and instance names.
        """

        raise NotImplementedError

    @classmethod
    def permission_predicate(cls, active_user, **instances):
        """
        Abstract method.

        Returns ``True`` iff the user has permission to access the view

        :param active_user: the active user that is trying to access the view
        :param instances: model instances fetched using path parameters
        """
        raise NotImplementedError

    @classmethod
    def view_has_permission(cls, method: str, active_user, **kwargs):
        """:meta private:"""

        logged_in = super().view_has_permission(method, active_user, **kwargs)

        if not logged_in:
            return False

        instances = {
            instance_name: model_class.objects.filter(
                pk=kwargs[path_parameter_name]
            ).first()
            for path_parameter_name, (
                model_class,
                instance_name,
            ) in cls.get_path_parameter_mapping().items()
        }

        # permit for non-existent instances, so we can return 404 on the actual request
        if any(instance is None for instance in instances.values()):
            return True

        return cls.permission_predicate(active_user=active_user, **instances)


class EventPermissionMixin(ObjectPermissionMixin):
    """
    Base mixin class for mixins that work with events.

    Path parameter primary key name is ``pk`` by default, or ``event_id_key`` if set.

    The event instance is passed as ``event`` in the :meth:`permission_predicate`.
    """

    @classmethod
    def get_path_parameter_mapping(cls):
        """:meta private:"""

        event_id_key_opt = getattr(cls, "event_id_key", None)

        event_id_key = event_id_key_opt if event_id_key_opt is not None else "pk"

        return {event_id_key: (Event, "event")}


class OccurrencePermissionMixin(ObjectPermissionMixin):
    """
    Permits users that can manage the occurence's event.

    Path parameter primary key name is ``occurence_id``.
    """

    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        """:meta private:"""

        return occurrence.event.can_user_manage(active_user)

    @classmethod
    def get_path_parameter_mapping(cls):
        """:meta private:"""

        return {"occurrence_id": (EventOccurrence, "occurrence")}


class OccurrenceManagePermissionMixinID(OccurrencePermissionMixin):
    """
    Permits users that can manage the occurence.

    Path parameter primary key name is ``occurence_id``.
    """

    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        """:meta private:"""

        return occurrence.can_user_manage(active_user)


class OccurrenceManagePermissionMixinPK(OccurrenceManagePermissionMixinID):
    """
    Permits users that can manage the occurence.

    Path parameter primary key name is ``pk``.
    """

    @classmethod
    def get_path_parameter_mapping(cls):
        """:meta private:"""

        return {"pk": (EventOccurrence, "occurrence")}


class EventManagePermissionMixin(EventPermissionMixin):
    """
    Permits users that can manage the event.

    Path parameter primary key name is ``pk`` by default, or ``event_id_key`` if set.
    """

    @classmethod
    def permission_predicate(cls, event, active_user):
        """:meta private:"""

        return event.can_user_manage(active_user)


class EventInteractPermissionMixin(EventPermissionMixin):
    """
    Permits users that can manage the event or interact with it.

    Path parameter primary key name is ``pk`` by default, or ``event_id_key`` if set.
    """

    @classmethod
    def permission_predicate(cls, event, active_user):
        """:meta private:"""

        return event.can_user_manage(active_user) or event.can_person_interact_with(
            active_user.person
        )


class UnenrollMyselfPermissionMixin(ObjectPermissionMixin):
    """
    Permits users that are associated with the same person as the enrollment.

    Path parameter primary key name is ``pk``.
    """

    @classmethod
    def get_path_parameter_mapping(cls):
        """:meta private:"""

        return {"pk": (ParticipantEnrollment, "enrollment")}

    @classmethod
    def permission_predicate(cls, enrollment, active_user):
        """:meta private:"""

        return enrollment.person == active_user.person


class OccurrenceEnrollOrganizerPermissionMixin(ObjectPermissionMixin):
    """
    Permits users that can enroll on a certain position in the occurrence.

    Path parameter primary key names are ``occurrence_id``
    and ``position_assignment_id``.
    """

    @classmethod
    def get_path_parameter_mapping(cls):
        """:meta private:"""

        return {
            "occurrence_id": (EventOccurrence, "occurrence"),
            "position_assignment_id": (EventPositionAssignment, "position_assignment"),
        }

    @classmethod
    def permission_predicate(cls, occurrence, position_assignment, active_user):
        """:meta private:"""

        return occurrence.can_enroll_position(active_user.person, position_assignment)


class OccurrenceUnenrollOrganizerPermissionMixin(ObjectPermissionMixin):
    """
    Permits users that can unenroll from a certain position in the occurrence.

    Path parameter primary key names are ``occurrence_id`` for the occurence
    and ``pk`` for the organizer assignment instance.
    """

    @classmethod
    def get_path_parameter_mapping(cls):
        """:meta private:"""

        return {
            "occurrence_id": (EventOccurrence, "occurrence"),
            "pk": (OrganizerAssignment, "organizer_assignment"),
        }

    @classmethod
    def permission_predicate(cls, occurrence, organizer_assignment, active_user):
        """:meta private:"""

        return occurrence.can_unenroll_position(
            active_user.person, organizer_assignment.position_assignment
        )
