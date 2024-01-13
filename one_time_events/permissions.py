from events.permissions import (
    EventCreatePermissionMixin,
    EventInteractPermissionMixin,
    OccurrenceManagePermissionMixinPK,
)
from one_time_events.models import OneTimeEvent


class OneTimeEventCreatePermissionMixin(EventCreatePermissionMixin):
    """
    POST: Users that manage the one-time event category sent in the request.
    GET: Users that manage at least one one-time event category.
    """

    permissions_formula_GET = [
        [OneTimeEvent.Category.COMMERCIAL],
        [OneTimeEvent.Category.COURSE],
        [OneTimeEvent.Category.FOR_CHILDREN],
        [OneTimeEvent.Category.PRESENTATION],
        [OneTimeEvent.Category.SOCIAL],
    ]


class OneTimeEventEnrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    """
    Permits users that can enroll as organizers of the event.
    """

    @classmethod
    def permission_predicate(cls, event, active_user):
        return event.can_enroll_organizer(active_user.person)


class OneTimeEventUnenrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    """
    Permits users that can unenroll as organizers of the event.
    """

    @classmethod
    def permission_predicate(cls, event, active_user):
        return event.can_unenroll_organizer(active_user.person)


class OccurrenceFillAttendancePermissionMixin(OccurrenceManagePermissionMixinPK):
    """
    Permits users that can fill the attendance of the event occurrence.
    """

    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_user_fill_attendance(active_user)


class OccurrenceDetailPermissionMixin(OccurrenceManagePermissionMixinPK):
    """
    Permits users that can manage the event occurrence or fill its attendance.
    """

    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_user_manage(
            active_user
        ) or occurrence.can_user_fill_attendance(active_user)
