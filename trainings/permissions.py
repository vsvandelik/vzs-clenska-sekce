from events.permissions import EventCreatePermissionMixin, OccurrencePermissionMixin
from trainings.models import Training


class TrainingCreatePermissionMixin(EventCreatePermissionMixin):
    """
    POST: Users that manage the training category sent in the request.
    GET: Users that manage at least one training category.
    """

    permissions_formula_GET = [
        [Training.Category.CLIMBING],
        [Training.Category.MEDICAL],
        [Training.Category.SWIMMING],
    ]


class OccurrenceExcuseMyselfOrganizerPermissionMixin(OccurrencePermissionMixin):
    """
    Permits users that can excuse themselves as a coach of the training occurrence.
    """

    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_coach_excuse(active_user.person)


class OccurrenceExcuseMyselfParticipantPermissionMixin(OccurrencePermissionMixin):
    """
    Permits users that can excuse themselves
    as a participant of the training occurrence.
    """

    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_participant_excuse(active_user.person)


class OccurrenceEnrollMyselfParticipantPermissionMixin(OccurrencePermissionMixin):
    """
    Permits users that can enroll themselves
    as a participant of the training occurrence.
    """

    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_participant_enroll(active_user.person)


class OccurrenceUnenrollMyselfParticipantPermissionMixin(OccurrencePermissionMixin):
    """
    Permits users that can unenroll themselves
    as a participant of the training occurrence.
    """

    @classmethod
    def permission_predicate(cls, occurrence, active_user):
        return occurrence.can_participant_unenroll(active_user.person)
