from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from events.models import (
    Event,
    EventOrOccurrenceState,
    EventOccurrence,
    ParticipantEnrollment,
    OrganizerPositionAssignment,
)
from trainings.models import Training
from vzs import settings


class OneTimeEvent(Event):
    class Category(models.TextChoices):
        COMMERCIAL = "komercni", _("komerční")
        COURSE = "kurz", _("kurz")
        PRESENTATION = "prezentacni", _("prezentační")

    enrolled_participants = models.ManyToManyField(
        "persons.Person",
        through="one_time_events.OneTimeEventParticipantEnrollment",
    )

    default_participation_fee = models.PositiveIntegerField(
        _("Standardní výše poplatku pro účastníky"), null=True, blank=True
    )
    category = models.CharField(
        _("Druh události"), max_length=11, choices=Category.choices
    )

    # if NULL -> no effect
    # else to enrollment in this event, you need to be approved participant of an arbitrary training of selected category
    training_category = models.CharField(
        null=True, max_length=10, choices=Training.Category.choices
    )

    state = models.CharField(max_length=10, choices=EventOrOccurrenceState.choices)

    def _occurrences_list(self):
        return OneTimeEventOccurrence.objects.filter(event=self)

    def occurrences_list(self):
        occurrences = self._occurrences_list()
        return occurrences

    def sorted_occurrences_list(self):
        occurrences = self._occurrences_list().order_by("date")
        return occurrences

    def approved_participants(self):
        return self.participants_by_state(ParticipantEnrollment.State.APPROVED)

    def waiting_participants(self):
        return self.participants_by_state(ParticipantEnrollment.State.WAITING)

    def substitute_participants(self):
        return self.participants_by_state(ParticipantEnrollment.State.SUBSTITUTE)

    def participants_by_state(self, state):
        output = []
        for enrolled_participant in self.enrolled_participants.all():
            enrollment = enrolled_participant.onetimeeventparticipantenrollment_set.get(
                one_time_event=self
            )
            if enrollment.state == state:
                output.append(enrolled_participant)
        return output

    def __str__(self):
        return self.name

    def get_default_participation_fee_display(self):
        if self.default_participation_fee is not None:
            return f"{self.default_participation_fee} Kč"
        return mark_safe(settings.VALUE_MISSING_HTML)


class OneTimeEventOccurrence(EventOccurrence):
    date = models.DateField(_("Den konání"))
    hours = models.PositiveSmallIntegerField(
        _("Počet hodin"), validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    organizers_assignment = models.ManyToManyField(
        "one_time_events.OneTimeEventOccurrenceOrganizerPositionAssignment",
        related_name="one_time_event_occurrence_organizer_position_assignment_set",
    )


class OneTimeEventOccurrenceOrganizerPositionAssignment(OrganizerPositionAssignment):
    one_time_event_ocurrence = models.ForeignKey(
        "one_time_events.OneTimeEventOccurrence", on_delete=models.CASCADE
    )


class OneTimeEventParticipantEnrollment(ParticipantEnrollment):
    one_time_event = models.ForeignKey(
        "one_time_events.OneTimeEvent", on_delete=models.CASCADE
    )
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    agreed_participation_fee = models.PositiveIntegerField(
        _("Poplatek za účast"), null=True, blank=True
    )

    @property
    def event(self):
        return self.one_time_event

    @event.setter
    def event(self, value):
        self.one_time_event = value
