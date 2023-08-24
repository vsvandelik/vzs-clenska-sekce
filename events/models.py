import polymorphic.models
from django.db import models
from django.utils.translation import gettext_lazy as _
from persons.models import Person
from features.models import Feature
from django.core.validators import MinValueValidator, MaxValueValidator
from polymorphic.models import PolymorphicModel
from polymorphic.managers import PolymorphicManager


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


class Event(PolymorphicModel):
    name = models.CharField(_("Název"), max_length=50)
    description = models.TextField(_("Popis"), null=True, blank=True)
    location = models.CharField(
        _("Místo konání"), null=True, blank=True, max_length=200
    )

    date_start = models.DateField(_("Začíná"))
    date_end = models.DateField(_("Končí"))

    positions = models.ManyToManyField(
        "positions.EventPosition",
        through="events.EventPositionAssignment",
        related_name="event_position_assignment_set",
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

    def can_person_enroll_as_participant(self, person):
        if person is None:
            return False
        if self.min_age is not None and self.min_age > person.age:
            return False
        if self.max_age is not None and self.max_age < person.age:
            return False
        if self.group is not None and not person.groups.contains(self.group):
            return False
        if (
            self.allowed_person_types.all().count() > 0
            and not self.allowed_person_types.contains(person.person_type)
        ):
            return False

        return True

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

    def enrollments_by_state(self, state):
        raise NotImplementedError

    def participants_by_state(self, state):
        return [enrollment.person for enrollment in self.enrollments_by_state(state)]

    def approved_enrollments(self):
        return self.enrollments_by_state(ParticipantEnrollment.State.APPROVED)

    def substitute_enrollments(self):
        return self.enrollments_by_state(ParticipantEnrollment.State.SUBSTITUTE)

    def rejected_enrollments(self):
        return self.enrollments_by_state(ParticipantEnrollment.State.REJECTED)

    def approved_participants(self):
        return self.participants_by_state(ParticipantEnrollment.State.APPROVED)

    def substitute_participants(self):
        return self.participants_by_state(ParticipantEnrollment.State.SUBSTITUTE)

    def rejected_participants(self):
        return self.participants_by_state(ParticipantEnrollment.State.REJECTED)


class EventOccurrence(PolymorphicModel):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)

    # These two fields contain person that were missing and their absence was not excused
    # Persons that were absent and were excused will be removed from participants or organizers
    missing_organizers_unexcused = models.ManyToManyField(
        "persons.Person", related_name="missing_organizers_set"
    )

    missing_participants_unexcused = models.ManyToManyField(
        "persons.Person", related_name="missing_participants_set"
    )
    state = models.CharField(max_length=10, choices=EventOrOccurrenceState.choices)

    def enrolled_organizers(self):
        pass  # TODO:


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


class OrganizerPositionAssignment(PolymorphicModel):
    position_assignment = models.ForeignKey(
        "events.EventPositionAssignment", on_delete=models.CASCADE
    )
    organizers = models.ManyToManyField("persons.Person")


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
