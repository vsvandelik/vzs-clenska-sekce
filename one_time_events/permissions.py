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
    def view_has_permission(
        cls, logged_in_user, active_person, occurrence_id, **kwargs
    ):
        for occurrence in EventOccurrence.objects.filter(pk=occurrence_id):
            return occurrence.event.can_enroll_organizer(active_person)
          
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_user_fill_attendance(logged_in_user)


class OccurrenceDetailPermissionMixin(OccurrenceManagePermissionMixin2):
    @classmethod
    def view_has_permission(
        cls, logged_in_user, active_person, occurrence_id, **kwargs
    ):
        for occurrence in EventOccurrence.objects.filter(pk=occurrence_id):
            return occurrence.event.can_unenroll_organizer(active_person)

        return False
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_user_manage(
            logged_in_user
        ) or occurrence.can_user_fill_attendance(logged_in_user)
