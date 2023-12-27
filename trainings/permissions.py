from events.permissions import OccurrencePermissionMixin


class OccurrenceExcuseMyselfOrganizerPermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_coach_excuse(active_user.person)


class OccurrenceExcuseMyselfParticipantPermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_participant_excuse(active_user.person)


class OccurrenceEnrollMyselfParticipantPermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_participant_enroll(active_user.person)


class OccurrenceUnenrollMyselfParticipantPermissionMixin(OccurrencePermissionMixin):
    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_participant_unenroll(active_user.person)
