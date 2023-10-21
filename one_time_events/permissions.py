from events.models import EventOccurrence
from events.permissions import EventInteractPermissionMixinBase
from users.views import PermissionRequiredMixin


class OneTimeEventEnrollOrganizerPermissionMixin(EventInteractPermissionMixinBase):
    @classmethod
    def _permission_predicate(cls, event, logged_in_user, active_person):
        return event.can_enroll_organizer(active_person)


class OneTimeEventUnenrollOrganizerPermissionMixin(EventInteractPermissionMixinBase):
    @classmethod
    def _permission_predicate(cls, event, logged_in_user, active_person):
        return event.can_unenroll_organizer(active_person)


class OccurrenceEnrollOrganizerPermissionMixin(PermissionRequiredMixin):
    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, occurrence_id):
        for occurrence in EventOccurrence.objects.filter(pk=occurrence_id):
            return occurrence.event.can_enroll_organizer(active_person)

        return False


class OccurrenceUnenrollOrganizerPermissionMixin(PermissionRequiredMixin):
    @classmethod
    def view_has_permission(cls, logged_in_user, active_person, occurrence_id):
        for occurrence in EventOccurrence.objects.filter(pk=occurrence_id):
            return occurrence.event.can_unenroll_organizer(active_person)

        return False
