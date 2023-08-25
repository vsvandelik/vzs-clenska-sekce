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
from transactions.models import Transaction
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
        "Kategorie tréninku",
        null=True,
        max_length=10,
        choices=Training.Category.choices,
    )

    state = models.CharField(max_length=10, choices=EventOrOccurrenceState.choices)

    def does_participant_satisfies_requirements(self, person):
        if not super().does_participant_satisfies_requirements(person):
            return False

        if (
            self.training_category is not None
            and not Training.does_person_attends_training_of_category(
                person, self.training_category
            )
        ):
            return False

        return True

    def has_free_spot(self):
        if self.participants_enroll_state == ParticipantEnrollment.State.APPROVED:
            return len(self.approved_participants()) < self.capacity
        elif self.participants_enroll_state == ParticipantEnrollment.State.SUBSTITUTE:
            return len(self.all_possible_participants()) < self.capacity
        raise NotImplementedError

    def can_participant_unenroll(self, person):
        if not super().can_participant_unenroll(person):
            return False

        enrollment = self.get_participant_enrollment(person)
        if enrollment.transaction is None:
            return True
        return not enrollment.transaction.is_settled

    def get_participant_enrollment(self, person):
        if person is None:
            return None
        try:
            return person.onetimeeventparticipantenrollment_set.get(one_time_event=self)
        except OneTimeEventParticipantEnrollment.DoesNotExist:
            return None

    def _occurrences_list(self):
        return OneTimeEventOccurrence.objects.filter(event=self)

    def occurrences_list(self):
        occurrences = self._occurrences_list()
        return occurrences

    def sorted_occurrences_list(self):
        occurrences = self._occurrences_list().order_by("date")
        return occurrences

    def enrollments_by_Q(self, condition):
        return self.onetimeeventparticipantenrollment_set.filter(condition)

    def __str__(self):
        return self.name


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
    person = models.ForeignKey(
        "persons.Person", verbose_name="Osoba", on_delete=models.CASCADE
    )
    agreed_participation_fee = models.PositiveIntegerField(
        _("Poplatek za účast*"), null=True, blank=True
    )
    transaction = models.ForeignKey(
        "transactions.Transaction", null=True, on_delete=models.SET_NULL
    )

    class Meta:
        unique_together = ["one_time_event", "person"]

    def delete(self):
        transaction = OneTimeEventParticipantEnrollment.objects.get(
            pk=self.pk
        ).transaction
        super().delete()
        if transaction is not None and not transaction.is_settled:
            transaction.delete()

    @staticmethod
    def create_attached_transaction(enrollment, event):
        fee = (
            -enrollment.agreed_participation_fee
            if enrollment.agreed_participation_fee is not None
            else -event.default_participation_fee
        )
        return Transaction(
            amount=fee,
            reason=f"Schválená přihláška na jednorázovou událost {event}",
            date_due=event.date_start,
            person=enrollment.person,
            event=event,
        )

    @property
    def event(self):
        return self.one_time_event

    @event.setter
    def event(self, value):
        self.one_time_event = value
