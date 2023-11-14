from datetime import datetime, timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel

from features.models import Feature, FeatureAssignment
from persons.models import Person
from vzs import settings


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


class Event(PolymorphicModel):
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

    @staticmethod
    def check_common_requirements(req_obj, person):
        person_with_age = Person.objects.with_age().get(id=person.id)

        missing_age = person_with_age.age is None and (
            req_obj.min_age is not None or req_obj.max_age is not None
        )

        min_age_out = req_obj.min_age is not None and (
            missing_age or req_obj.min_age > person_with_age.age
        )
        max_age_out = req_obj.max_age is not None and (
            missing_age or req_obj.max_age < person_with_age.age
        )
        group_unsatisfied = (
            req_obj.group is not None and req_obj.group not in person.groups.all()
        )
        allowed_person_types_unsatisfied = (
            req_obj.allowed_person_types.exists()
            and not req_obj.allowed_person_types.contains(
                EventPersonTypeConstraint.get_or_create(person.person_type)
            )
        )

        if (
            missing_age
            or min_age_out
            or max_age_out
            or group_unsatisfied
            or allowed_person_types_unsatisfied
        ):
            return False

        return True

    def does_participant_satisfy_requirements(self, person):
        return self.check_common_requirements(self, person)

    def has_free_spot(self):
        return self.capacity is None

    def can_person_enroll_as_participant(self, person):
        return (
            self.can_person_enroll_as_waiting(person)
            and self.has_free_spot()
            and datetime.now().date()
            + timedelta(days=settings.PARTICIPANT_ENROLL_DEADLINE_DAYS)
            <= self.date_start
        )

    def can_person_enroll_as_waiting(self, person):
        if person is None or person in self.enrolled_participants.all():
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

    def enrollments_by_Q(self, state):
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
            self.can_person_enroll_as_waiting(person)
            or self.can_person_enroll_as_participant(person)
            or self.can_participant_unenroll(person)
            or person in self.enrolled_participants.all()
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


class EventOccurrence(PolymorphicModel):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    state = models.CharField(max_length=10, choices=EventOrOccurrenceState.choices)

    def position_organizers(self, position_assignment):
        raise NotImplementedError

    def has_position_free_spot(self, position_assignment):
        raise NotImplementedError

    def satisfies_position_requirements(self, person, position_assignment):
        if not Event.check_common_requirements(position_assignment.position, person):
            return False

        features = position_assignment.position.required_features

        feature_type_conditions = [
            Q(feature_type=Feature.Type.QUALIFICATION),
            Q(feature_type=Feature.Type.PERMISSION),
            Q(feature_type=Feature.Type.EQUIPMENT),
        ]

        for condition in feature_type_conditions:
            observed_features = features.filter(condition)
            if observed_features.exists():
                assignment = FeatureAssignment.objects.filter(
                    Q(feature__in=observed_features)
                    & Q(person=person)
                    & Q(date_assigned__lte=self.event.date_start)
                    & Q(date_returned=None)
                    & (Q(date_expire=None) | Q(date_expire__gte=self.event.date_start))
                ).first()
                if assignment is None:
                    return False
        return True

    def is_organizer_of_position(self, person, position_assignment):
        return self.get_organizer_assignment(person, position_assignment) is not None

    def get_organizer_assignment(self, person, position_assignment):
        assignments = self.position_organizers(position_assignment)
        return assignments.filter(person=person).first()

    def can_enroll_position(self, person, position_assignment):
        no_free_spot = not self.has_position_free_spot(position_assignment)
        organizer_of_position = self.is_organizer_of_position(
            person, position_assignment
        )

        if no_free_spot or organizer_of_position:
            return False

        return self.satisfies_position_requirements(person, position_assignment)

    def can_unenroll_position(self, person, position_assignment):
        return self.is_organizer_of_position(person, position_assignment)

    def attending_participants_attendance(self):
        raise NotImplementedError

    def attendace_not_filled_when_should(self):
        return (
            self.can_attendance_be_filled()
            and self.state == EventOrOccurrenceState.OPEN
        )

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
