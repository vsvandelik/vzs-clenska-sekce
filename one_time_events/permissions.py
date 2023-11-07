from events.permissions import EventInteractPermissionMixin, OccurrencePermissionMixin


class OneTimeEventEnrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    @classmethod
    def predicate(cls, event, logged_in_user, active_person):
        return event.can_enroll_organizer(active_person)


class OneTimeEventUnenrollOrganizerPermissionMixin(EventInteractPermissionMixin):
    @classmethod
    def predicate(cls, event, logged_in_user, active_person):
        return event.can_unenroll_organizer(active_person)


class OccurrenceEnrollOrganizerPermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.event.can_enroll_organizer(active_person)


class OccurrenceUnenrollOrganizerPermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.event.can_unenroll_organizer(active_person)


class OccurenceManagePermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def get_primary_key_name(cls):
        return "pk"

    @classmethod
    def predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_user_manage(logged_in_user)


class OccurenceFillAttendancePermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def get_primary_key_name(cls):
        return "pk"

    @classmethod
    def predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_user_fill_attendance(logged_in_user)
