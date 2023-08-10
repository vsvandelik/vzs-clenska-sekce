from django.db import models
from django.utils.translation import gettext_lazy as _
from persons.models import Person
from features.models import Feature
from django.core.validators import MinValueValidator, MaxValueValidator


class TrainingCategory(models.TextChoices):
    CLIMBING = "lezecky", _("lezecký")
    SWIMMING = "plavecky", _("plavecký")
    MEDICAL = "zdravoveda", _("zdravověda")


class Event(models.Manager):
    name = models.CharField(_("Název"), max_length=50)
    description = models.TextField(_("Popis"))
    location = models.CharField(_("Místo konání"), max_length=200)

    positions = models.ManyToManyField(
        "positions.EventPosition", through="events.EventPositionAssignment"
    )

    # requirements for participants
    capacity = models.PositiveSmallIntegerField(
        _("Maximální počet účastníků"), null=True
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
    allowed_person_types = models.ManyToManyField("persons.PersonType")

    # if NULL -> no effect
    # else to enrollment in this event, you need to be approved participant of an arbitrary training of selected type
    participants_of_specific_training_requirement = models.CharField(
        max_length=10, choices=TrainingCategory.choices
    )

    class Meta:
        abstract = True


class EventOccurrence(models.Manager):
    class State(models.TextChoices):
        FUTURE = "neuzavrena", _("neuzavřena")
        FINISHED = "uzavrena", _("uzavřena")
        APPROVED = "schvalena", _("schválena")

    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)

    missing_organizers = models.ManyToManyField("persons.Person")

    missing_participants = models.ManyToManyField("persons.Person")

    organizers = models.ManyToManyField(
        "persons.Person", through="events.EventOccurrenceOrganizerPositionAssignment"
    )

    state = models.CharField(max_length=10, choices=State.choices)

    def enrolled_organizers(self):
        pass  # TODO:


class Enrollment(models.Manager):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    datetime = models.DateTimeField()


class ParticipantEnrollment(Enrollment):
    class State(models.TextChoices):
        WAITING = "ceka", _("čeká")
        APPROVED = "schvalen", _("schválen")
        SUBSTITUTE = "nahradnik", _("nahradník")

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    state = models.CharField(max_length=10, choices=State.choices)


class EventPositionAssignment(models.Model):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    position = models.ForeignKey("positions.EventPosition", on_delete=models.CASCADE)
    count = models.PositiveSmallIntegerField(
        _("Počet"), default=1, validators=[MinValueValidator(1)]
    )

    class Meta:
        unique_together = ["event", "position"]


class EventOccurrenceOrganizerPositionAssignment(models.Model):
    event_occurrence = models.ForeignKey(
        "events.EventOccurrence", on_delete=models.CASCADE
    )
    position_assignment = models.ForeignKey(
        "positions.EventPosition", on_delete=models.CASCADE
    )
    organizers = models.ManyToManyField("persons.Person")

    class Meta:
        unique_together = ["event_occurrence", "position_assignment"]
