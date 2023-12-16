from datetime import timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _
from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel

from events.utils import check_common_requirements
from features.models import Feature, FeatureAssignment
from persons.models import Person
from vzs import settings
from vzs.models import RenderableModelMixin
from vzs.settings import CURRENT_DATE


class EventOrOccurrenceState(models.TextChoices):
    # attendance not filled
    OPEN = "neuzavrena", _("neuzavřena")

    # attendance filled for both organizers and participants
    CLOSED = "uzavrena", _("uzavřena")

    # transaction issued
    COMPLETED = "zpracovana", _("zpracována")


class ParticipantEnrollment(PolymorphicModel):
    class State(models.TextChoices):
        APPROVED = "schvalen", _("schválen")
        SUBSTITUTE = "nahradnik", _("nahradník")
        REJECTED = "odmitnut", _("odmítnut")

    objects = PolymorphicManager()

    created_datetime = models.DateTimeField()
    state = models.CharField("Stav přihlášky", max_length=10, choices=State.choices)


class Event(RenderableModelMixin, PolymorphicModel):
    name = models.CharField(_("Název"), max_length=50)
    description = models.TextField(_("Popis"), null=True, blank=True)
    location = models.CharField(
        _("Místo konání"), null=True, blank=True, max_length=200
    )

    date_start = models.DateField(_("Začíná"))
    date_end = models.DateField(_("Končí"))

    positions = models.ManyToManyField(
        "positions.EventPosition", through="events.EventPositionAssignment"
    )

    participants_enroll_state = models.CharField(
        "Přidat nové účastníky jako",
        max_length=10,
        default=ParticipantEnrollment.State.SUBSTITUTE.value,
        choices=[
            (
                ParticipantEnrollment.State.SUBSTITUTE.value,
                ParticipantEnrollment.State.SUBSTITUTE.label,
            ),
            (
                ParticipantEnrollment.State.APPROVED.value,
                ParticipantEnrollment.State.APPROVED.label,
            ),
        ],
    )

    # requirements for participants
    capacity = models.PositiveSmallIntegerField(
        _("Maximální počet účastníků"), null=True, blank=True
    )
    min_age = models.PositiveSmallIntegerField(
        _("Minimální věk účastníků"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )

    max_age = models.PositiveSmallIntegerField(
        _("Maximální věk účastníků"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )

    group = models.ForeignKey(
        "groups.Group", null=True, verbose_name="Skupina", on_delete=models.SET_NULL
    )

    # if NULL -> no effect (all person types are allowed)
    allowed_person_types = models.ManyToManyField(
        "events.EventPersonTypeConstraint",
        related_name="event_person_type_constraint_set",
    )

    def is_one_time_event(self):
        from one_time_events.models import OneTimeEvent

        return isinstance(self, OneTimeEvent)

    def is_training(self):
        from trainings.models import Training

        return isinstance(self, Training)

    def get_capacity_display(self):
        if self.capacity is None:
            return "∞"
        return self.capacity

    def position_assignments_sorted(self):
        return self.eventpositionassignment_set.order_by("position__name")

    def does_participant_satisfy_requirements(self, person):
        return check_common_requirements(self, person)

    def has_free_spot(self):
        return self.capacity is None

    def has_approved_participant(self):
        raise NotImplementedError

    def has_organizer(self):
        raise NotImplementedError

    def can_person_enroll_as_participant(self, person):
        return (
            self.can_person_enroll_as_waiting(person)
            and self.has_free_spot()
            and CURRENT_DATE()
            + timedelta(days=settings.PARTICIPANT_ENROLL_DEADLINE_DAYS)
            <= self.date_start
        )

    def can_person_enroll_as_waiting(self, person):
        if (
            person is None
            or self.enrolled_participants.contains(person)
            or self.capacity == 0
            or CURRENT_DATE() > self.date_end
        ):
            return False

        return self.does_participant_satisfy_requirements(person)

    def can_participant_unenroll(self, person):
        enrollment = self.get_participant_enrollment(person)
        if enrollment is None or enrollment.state in [
            ParticipantEnrollment.State.APPROVED,
            ParticipantEnrollment.State.REJECTED,
        ]:
            return False
        return True

    def get_participant_enrollment(self, person):
        raise NotImplementedError

    def occurrences_list(self):
        raise NotImplementedError

    def sorted_occurrences_list(self):
        raise NotImplementedError

    def enrollments_by_Q(self, state) -> QuerySet[ParticipantEnrollment]:
        raise NotImplementedError

    def participants_by_Q(self, condition):
        return [enrollment.person for enrollment in self.enrollments_by_Q(condition)]

    def approved_enrollments(self):
        return self.enrollments_by_Q(Q(state=ParticipantEnrollment.State.APPROVED))

    def substitute_enrollments(self):
        return self.enrollments_by_Q(Q(state=ParticipantEnrollment.State.SUBSTITUTE))

    def rejected_enrollments(self):
        return self.enrollments_by_Q(Q(state=ParticipantEnrollment.State.REJECTED))

    def all_possible_participants(self):
        return self.participants_by_Q(
            Q(state=ParticipantEnrollment.State.APPROVED)
            | Q(state=ParticipantEnrollment.State.SUBSTITUTE)
        )

    def approved_participants(self):
        return self.participants_by_Q(Q(state=ParticipantEnrollment.State.APPROVED))

    def substitute_participants(self):
        return self.participants_by_Q(Q(state=ParticipantEnrollment.State.SUBSTITUTE))

    def rejected_participants(self):
        return self.participants_by_Q(Q(state=ParticipantEnrollment.State.REJECTED))

    def substitute_enrollments_2_capacity(self):
        raise NotImplementedError

    def can_person_interact_with(self, person):
        return (
            self.is_organizer(person)
            or self.can_person_enroll_as_waiting(person)
            or (
                CURRENT_DATE() <= self.date_end
                and any(
                    [
                        position.does_person_satisfy_requirements(
                            person, self.date_start
                        )
                        for position in self.positions.all()
                    ]
                )
            )
        )

    def can_user_manage(self, user):
        return user.has_perm(f"{type(self)._meta.app_label}.{self.category}")

    def exists_occurrence_with_unfilled_attendance(self):
        return any(
            (
                occurrence.attendace_not_filled_when_should()
                for occurrence in self.eventoccurrence_set.all()
            )
        )

    def can_enroll_unenroll_organizer(self, person, enroll_unenroll_func):
        if person is None:
            return False

        for occurrence in self.eventoccurrence_set.all():
            for position_assignment in self.eventpositionassignment_set.all():
                if enroll_unenroll_func(occurrence, person, position_assignment):
                    return True
        return False

    def is_organizer(self, person):
        return NotImplementedError

    def does_person_satisfy_position_requirements(self, person, position):
        raise NotImplementedError


class EventOccurrence(PolymorphicModel):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    state = models.CharField(max_length=10, choices=EventOrOccurrenceState.choices)

    def get_person_organizer_assignment(self, person):
        return self.organizeroccurrenceassignment_set.filter(person=person)

    def position_organizers(self, position_assignment):
        raise NotImplementedError

    def has_attending_organizer(self):
        raise NotImplementedError

    def has_attending_participant(self):
        raise NotImplementedError

    def has_position_free_spot(self, position_assignment):
        raise NotImplementedError

    def is_organizer_of_position(self, person, position_assignment):
        return self.get_organizer_assignment(person, position_assignment) is not None

    def get_organizer_assignment(self, person, position_assignment):
        assignments = self.position_organizers(position_assignment)
        return assignments.filter(person=person).first()

    def can_enroll_position(self, person, position_assignment):
        if (
            not self.can_position_be_still_enrolled()
            or not self.has_position_free_spot(position_assignment)
            or self.get_person_organizer_assignment(person).exists()
        ):
            return False

        return self.event.does_person_satisfy_position_requirements(
            person, position_assignment.position
        )

    def can_unenroll_position(self, person, position_assignment):
        if (
            not self.can_position_be_still_unenrolled()
            or not self.is_organizer_of_position(person, position_assignment)
        ):
            return False

        return True

    def attending_participants_attendance(self):
        raise NotImplementedError

    def attendace_not_filled_when_should(self):
        return (
            self.can_attendance_be_filled()
            and self.state == EventOrOccurrenceState.OPEN
        )

    def can_position_be_still_enrolled(self):
        raise NotImplementedError

    def can_position_be_still_unenrolled(self):
        raise NotImplementedError

    @property
    def is_opened(self):
        return self.state == EventOrOccurrenceState.OPEN

    @property
    def is_closed(self):
        return self.state == EventOrOccurrenceState.CLOSED

    @property
    def is_approved(self):
        return self.state == EventOrOccurrenceState.COMPLETED

    def can_user_manage(self, user):
        return self.event.can_user_manage(user)

    def can_user_fill_attendance(self, user):
        return self.can_user_manage(user)  # TODO: implement


class EventPositionAssignment(models.Model):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    position = models.ForeignKey(
        "positions.EventPosition", verbose_name="Pozice", on_delete=models.CASCADE
    )
    count = models.PositiveSmallIntegerField(
        _("Počet organizátorů"), default=1, validators=[MinValueValidator(1)]
    )

    def duplicate(self, event):
        position_assignment = EventPositionAssignment(
            event=event, position=self.position, count=self.count
        )
        position_assignment.save()
        return position_assignment

    class Meta:
        unique_together = ["event", "position"]

    def __str__(self):
        return self.position.name


class OrganizerAssignment(PolymorphicModel):
    transaction = models.ForeignKey(
        "transactions.Transaction", null=True, on_delete=models.SET_NULL
    )

    def can_unenroll(self):
        return self.occurrence.can_unenroll_position(
            self.person, self.position_assignment
        )

    def is_transaction_settled(self):
        return self.transaction is not None and self.transaction.is_settled


class EventPersonTypeConstraint(models.Model):
    person_type = models.CharField(
        _("Typ osoby"), unique=True, max_length=10, choices=Person.Type.choices
    )

    @staticmethod
    def get_or_create(person_type):
        return EventPersonTypeConstraint.objects.get_or_create(
            person_type=person_type, defaults={"person_type": person_type}
        )[0]

    def __str__(self):
        return self.get_person_type_display()
