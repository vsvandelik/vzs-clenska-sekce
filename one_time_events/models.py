from django.db import models
from events.models import (
    Event,
    EventOrOccurrenceState,
    EventOccurrence,
    ParticipantEnrollment,
    OrganizerPositionAssignment,
)
from trainings.models import Training
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.db.models import Q


class OneTimeEvent(Event):
    class Category(models.TextChoices):
        COMMERCIAL = "komercni", _("komerční")
        COURSE = "kurz", _("kurz")
        PRESENTATION = "prezentacni", _("prezentační")

    enrolled_participants = models.ManyToManyField(
        "persons.Person",
        through="one_time_events.OneTimeEventParticipantEnrollment",
        related_name="one_time_event_participant_enrollment_set",
    )

    default_participation_fee = models.PositiveIntegerField(
        _("Poplatek za účast"), null=True, blank=True
    )
    category = models.CharField(
        _("Druh události"), max_length=11, choices=Category.choices
    )

    # if NULL -> no effect
    # else to enrollment in this event, you need to be approved participant of an arbitrary training of selected type
    participants_of_specific_training_requirement = models.CharField(
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
            enrollment = enrolled_participant.training_participant_enrollment_set.get(
                one_time_event=self
            )
            if enrollment.state == state:
                output.append(enrolled_participant)
        return output


class OneTimeEventOccurrence(EventOccurrence):
    date = models.DateField(_("Den konání"))
    hours = models.PositiveSmallIntegerField(
        _("Počet hodin"), validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    organizers_assignment = models.ManyToManyField(
        "one_time_events.OneTimeEventOccurrenceOrganizerPositionAssignment"
    )


class OneTimeEventOccurrenceOrganizerPositionAssignment(OrganizerPositionAssignment):
    one_time_event_ocurrence = models.ForeignKey(
        "one_time_events.OneTimeEventOccurrence", on_delete=models.CASCADE
    )


class OneTimeEventParticipantEnrollment(ParticipantEnrollment):
    one_time_event = models.ForeignKey(
        "one_time_events.OneTimeEvent", on_delete=models.CASCADE
    )
    agreed_participation_fee = models.PositiveIntegerField(_("Poplatek za účast"))
