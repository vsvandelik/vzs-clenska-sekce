from events.permissions import (
    EventInteractPermissionMixin,
    OccurrenceManagePermissionMixin2,
)


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
        return occurrence.can_user_fill_attendance(active_person.get_user())


class OccurrenceDetailPermissionMixin(OccurrenceManagePermissionMixin2):
    @classmethod
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_user_manage(
            active_person.get_user()
        ) or occurrence.can_user_fill_attendance(active_person.get_user())
