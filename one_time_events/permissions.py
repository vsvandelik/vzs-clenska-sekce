from events.permissions import (
    EventInteractPermissionMixin,
    OccurrenceManagePermissionMixin2,
)


class OneTimeEventEnrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, active_user):
        return event.can_enroll_organizer(active_user.person)


class OneTimeEventUnenrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, active_user):
        return event.can_unenroll_organizer(active_user.person)


class OccurrenceFillAttendancePermissionMixin(OccurrenceManagePermissionMixin2):
    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_user_fill_attendance(active_user)


class OccurrenceDetailPermissionMixin(OccurrenceManagePermissionMixin2):
    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_user_manage(
            active_user
        ) or occurrence.can_user_fill_attendance(active_user)
