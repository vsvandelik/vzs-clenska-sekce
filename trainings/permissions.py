from events.permissions import OccurrencePermissionMixin


class OccurrenceExcuseMyselfOrganizerPermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_coach_excuse(active_person)


class OccurrenceExcuseMyselfParticipantPermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_participant_excuse(active_person)


class OccurrenceEnrollMyselfParticipantPermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_participant_enroll(active_person)


class OccurrenceUnenrollMyselfParticipantPermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, logged_in_user, active_person):
        return occurrence.can_participant_unenroll(active_person)
