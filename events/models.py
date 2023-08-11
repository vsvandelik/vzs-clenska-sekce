from django.db import models
from django.utils.translation import gettext_lazy as _
from persons.models import Person
from features.models import Feature
from django.core.validators import MinValueValidator, MaxValueValidator
from polymorphic.models import PolymorphicModel


class TrainingCategory(models.TextChoices):
    CLIMBING = "lezecky", _("lezecký")
    SWIMMING = "plavecky", _("plavecký")
    MEDICAL = "zdravoveda", _("zdravověda")


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
    allowed_person_types = models.ManyToManyField("persons.PersonType")

    # if NULL -> no effect
    # else to enrollment in this event, you need to be approved participant of an arbitrary training of selected type
    participants_of_specific_training_requirement = models.CharField(
        null=True, max_length=10, choices=TrainingCategory.choices
    )

    def is_one_time_event(self):
        from one_time_events.models import OneTimeEvent

        return isinstance(self, OneTimeEvent)

    def is_training(self):
        from trainings.models import Training

        return isinstance(self, Training)

    def occurrences_list(self):
        return EventOccurrence.objects.filter(event=self)


class EventOccurrence(PolymorphicModel):
    class State(models.TextChoices):
        FUTURE = "neuzavrena", _("neuzavřena")
        FINISHED = "uzavrena", _("uzavřena")
        APPROVED = "schvalena", _("schválena")

    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)

    missing_organizers = models.ManyToManyField(
        "persons.Person", related_name="missing_organizers_set"
    )

    missing_participants = models.ManyToManyField(
        "persons.Person", related_name="missing_participants_set"
    )

    organizers_assignment = models.ManyToManyField(
        "events.EventOccurrenceOrganizerPositionAssignment"
    )

    state = models.CharField(max_length=10, choices=State.choices)

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
