from django.db import models
from django.utils.translation import gettext_lazy as _
from persons.models import Person
from features.models import Feature
from django.core.validators import MinValueValidator, MaxValueValidator
from polymorphic.models import PolymorphicModel


class EventOrOccurrenceState(models.TextChoices):
    # attendance not filled
    OPEN = "neuzavrena", _("neuzavřena")

    # attendance filled for both organizers and participants
    CLOSED = "uzavrena", _("uzavřena")

    # transaction issued
    COMPLETED = "zpracovana", _("zpracována")


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

    group = models.ForeignKey("groups.Group", null=True, on_delete=models.SET_NULL)

    # if NULL -> no effect (all person types are allowed)
    allowed_person_types = models.ManyToManyField("events.EventPersonTypeConstraint")

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


class Enrollment(PolymorphicModel):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    datetime = models.DateTimeField()


class ParticipantEnrollment(Enrollment):
    class State(models.TextChoices):
        WAITING = "ceka", _("čeká")
        APPROVED = "schvalen", _("schválen")
        SUBSTITUTE = "nahradnik", _("nahradník")

    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    state = models.CharField(max_length=10, choices=State.choices)


class EventPositionAssignment(models.Model):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    position = models.ForeignKey("positions.EventPosition", on_delete=models.CASCADE)
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
    def get_or_create_person_type(person_type):
        return EventPersonTypeConstraint.objects.get_or_create(
            person_type=person_type, defaults={"person_type": person_type}
        )[0]

    def __str__(self):
        return self.get_person_type_display()
