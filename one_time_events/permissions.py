from events.permissions import (
    EventCreatePermissionMixin,
    EventInteractPermissionMixin,
    OccurrenceManagePermissionMixinPK,
)
from one_time_events.models import OneTimeEvent


class OneTimeEventCreatePermissionMixin(EventCreatePermissionMixin):
    permissions_formula_GET = [
        [OneTimeEvent.Category.COMMERCIAL],
        [OneTimeEvent.Category.COURSE],
        [OneTimeEvent.Category.FOR_CHILDREN],
        [OneTimeEvent.Category.PRESENTATION],
        [OneTimeEvent.Category.SOCIAL],
    ]


class OneTimeEventEnrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, active_user):
        return event.can_enroll_organizer(active_user.person)


class OneTimeEventUnenrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    @classmethod
    def permission_predicate(cls, event, active_user):
        return event.can_unenroll_organizer(active_user.person)


class OccurrenceFillAttendancePermissionMixin(OccurrenceManagePermissionMixinPK):
    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_user_fill_attendance(active_user)


class OccurrenceDetailPermissionMixin(OccurrenceManagePermissionMixinPK):
    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_user_manage(
            active_user
        ) or occurrence.can_user_fill_attendance(active_user)
