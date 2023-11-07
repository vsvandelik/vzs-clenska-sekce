from events.models import EventOccurrence
from events.permissions import EventInteractPermissionMixin, OccurrencePermissionMixin


class OneTimeEventEnrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, logged_in_user, active_person):
        return event.can_enroll_organizer(active_person)


class OneTimeEventUnenrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, logged_in_user, active_person):
        return event.can_unenroll_organizer(active_person)


class OccurenceManagePermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_user_manage(logged_in_user)


class OccurenceManagePermissionMixin2(OccurenceManagePermissionMixin):
    @classmethod
    def get_path_parameter_mapping(cls):
        return {"pk": (EventOccurrence, "occurrence")}


class OccurenceFillAttendancePermissionMixin(OccurenceManagePermissionMixin2):
    @classmethod
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_user_fill_attendance(logged_in_user)


class OccurenceDetailPermissionMixin(OccurenceManagePermissionMixin2):
    @classmethod
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_user_manage(
            logged_in_user
        ) or occurrence.can_user_fill_attendance(logged_in_user)
