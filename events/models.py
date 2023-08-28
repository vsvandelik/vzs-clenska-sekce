from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel

from features.models import Feature
from persons.models import Person


class EventOrOccurrenceState(models.TextChoices):
    # attendance not filled
    OPEN = "neuzavrena", _("neuzavřena")

    # attendance filled for both organizers and participants
    CLOSED = "uzavrena", _("uzavřena")

    # transaction issued
    COMPLETED = "zpracovana", _("zpracována")


class ParticipantEnrollmentApprovedManager(PolymorphicManager):
    def get_queryset(self):
        return super().get_queryset().filter(state=ParticipantEnrollment.State.APPROVED)


class ParticipantEnrollmentSubstituteManager(PolymorphicManager):
    def get_queryset(self):
        return (
            super().get_queryset().filter(state=ParticipantEnrollment.State.SUBSTITUTE)
        )


class ParticipantEnrollmentRejectedManager(PolymorphicManager):
    def get_queryset(self):
        return super().get_queryset().filter(state=ParticipantEnrollment.State.REJECTED)


class ParticipantEnrollment(PolymorphicModel):
    class State(models.TextChoices):
        APPROVED = "schvalen", _("schválen")
        SUBSTITUTE = "nahradnik", _("nahradník")
        REJECTED = "odmitnut", _("odmítnut")

    objects = PolymorphicManager()
    enrollments_approved = ParticipantEnrollmentApprovedManager()
    enrollments_substitute = ParticipantEnrollmentSubstituteManager()
    enrollments_rejected = ParticipantEnrollmentRejectedManager()

    created_datetime = models.DateTimeField()
    state = models.CharField("Stav přihlášky", max_length=10, choices=State.choices)

    def delete(self):
        for occurrence in self.event.eventoccurrence_set.all():
            occurrence.attending_participants.remove(self.person)
        return super().delete()


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

    def does_participant_satisfy_requirements(self, person):
        person_with_age = Person.objects.with_age().get(id=person.id)

        if person_with_age.age is None and (
            self.min_age is not None or self.max_age is not None
        ):
            return False

        if self.min_age is not None and self.min_age > person_with_age.age:
            return False
        if self.max_age is not None and self.max_age < person_with_age.age:
            return False

        if self.group is not None and not person.groups.contains(self.group):
            return False
        if (
            self.allowed_person_types.exists()
            and not self.allowed_person_types.contains(
                EventPersonTypeConstraint.get_or_create(person.person_type)
            )
        ):
            return False

        return True

    def has_free_spot(self):
        return self.capacity is None

    def can_person_enroll_as_participant(self, person):
        return self.can_person_enroll_as_waiting(person) and self.has_free_spot()

    def can_person_enroll_as_waiting(self, person):
        if person is None:
            return False

        if self.enrolled_participants.contains(person):
            return False

        return self.does_participant_satisfy_requirements(person)

    def can_participant_unenroll(self, person):
        enrollment = self.get_participant_enrollment(person)
        if enrollment is None:
            return False
        if enrollment.state in [
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

    def organizers_assignments(self):
        return OrganizerOccurrenceAssignment.objects.filter(
            position__in=self.positions.all()
        )


class EventOccurrence(PolymorphicModel):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)

    organizers = models.ManyToManyField(
        "persons.Person",
        through="events.OrganizerOccurrenceAssignment",
    )

    attending_participants = models.ManyToManyField(
        "persons.Person", related_name="missing_participants_set"
    )
    state = models.CharField(max_length=10, choices=EventOrOccurrenceState.choices)


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


class OrganizerOccurrenceAssignment(models.Model):
    position_assignment = models.ForeignKey(
        "events.EventPositionAssignment",
        verbose_name="Pozice události",
        on_delete=models.CASCADE,
    )
    person = models.ForeignKey(
        "persons.Person", verbose_name="Osoba", on_delete=models.CASCADE
    )
    occurrence = models.ForeignKey("events.EventOccurrence", on_delete=models.CASCADE)
    transaction = models.ForeignKey(
        "transactions.Transaction", null=True, on_delete=models.SET_NULL
    )

    class Meta:
        unique_together = ["person", "occurrence"]


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
