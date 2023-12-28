from events.permissions import (
    EventInteractPermissionMixin,
    OccurrenceManagePermissionMixin2,
)
from persons.models import get_active_user


class OneTimeEventEnrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, logged_in_user, active_person):
        return event.can_enroll_organizer(active_person)


class OneTimeEventUnenrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, logged_in_user, active_person):
        return event.can_unenroll_organizer(active_person)


class OccurrenceFillAttendancePermissionMixin(OccurrenceManagePermissionMixin2):
    @classmethod
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_user_fill_attendance(get_active_user(active_person))


class OccurrenceDetailPermissionMixin(OccurrenceManagePermissionMixin2):
    @classmethod
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_user_manage(
            get_active_user(active_person)
        ) or occurrence.can_user_fill_attendance(get_active_user(active_person))
