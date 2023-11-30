from datetime import datetime, timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.models import (
    Event,
    EventOccurrence,
    EventOrOccurrenceState,
    OrganizerAssignment,
    ParticipantEnrollment,
)
from persons.models import PersonHourlyRate
from trainings.models import Training
from transactions.models import Transaction
from vzs import settings


class OneTimeEventAttendance(models.TextChoices):
    PRESENT = "prezence", _("prezence")
    MISSING = "absence", _("absence")


class OneTimeEvent(Event):
    class Category(models.TextChoices):
        COMMERCIAL = "komercni", _("komerční")
        COURSE = "kurz", _("kurz")
        PRESENTATION = "prezentacni", _("prezentační")
        FOR_CHILDREN = "pro-deti", _("pro děti")

    class Meta:
        permissions = [
            ("komercni", _("Správce komerčních akcí")),
            ("kurz", _("Správce kurzů")),
            ("prezentacni", _("Správce prezentačních akcí")),
        ]

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

    def does_participant_satisfy_requirements(self, person):
        if not super().does_participant_satisfy_requirements(person):
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
        possibly_free = super().has_free_spot()
        if not possibly_free:
            if self.participants_enroll_state == ParticipantEnrollment.State.APPROVED:
                return len(self.approved_participants()) < self.capacity
            elif (
                self.participants_enroll_state == ParticipantEnrollment.State.SUBSTITUTE
            ):
                return len(self.all_possible_participants()) < self.capacity
            raise NotImplementedError
        return True

    def has_approved_participant(self):
        return self.onetimeeventparticipantenrollment_set.filter(
            state=ParticipantEnrollment.State.APPROVED
        ).exists()

    def has_organizer(self):
        for occurrence in self.eventoccurrence_set.all():
            if occurrence.organizers.count() > 0:
                return True
        return False

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

    def organizer_persons(self):
        persons = set()
        assignments = OrganizerOccurrenceAssignment.objects.filter(
            occurrence__in=self.eventoccurrence_set.all()
        )
        for assignment in assignments:
            persons.add(assignment.person)
        return persons

    def __str__(self):
        return self.name

    def substitute_enrollments_2_capacity(self):
        enrollments = self.substitute_enrollments().order_by("created_datetime")
        take = len(enrollments)
        if self.capacity is not None:
            take = self.capacity - len(self.approved_participants())
        return enrollments[:take]

    def can_enroll_unenroll_organizer(self, person, enroll_unenroll_func):
        if person is None:
            return False

        for occurrence in self.eventoccurrence_set.all():
            for position_assignment in self.eventpositionassignment_set.all():
                if enroll_unenroll_func(occurrence, person, position_assignment):
                    return True
        return False

    def can_unenroll_organizer(self, person):
        return self.can_enroll_unenroll_organizer(
            person, OneTimeEventOccurrence.can_unenroll_position
        )

    def can_enroll_organizer(self, person):
        return self.can_enroll_unenroll_organizer(
            person, OneTimeEventOccurrence.can_enroll_position
        )

    def is_organizer(self, person):
        return OrganizerOccurrenceAssignment.objects.filter(
            occurrence__event=self, person=person
        ).exists()

    def can_person_interact_with(self, person):
        return (
            self.can_enroll_organizer(person)
            or self.can_unenroll_organizer(person)
            or super().can_person_interact_with(person)
        )

    def exists_closed_occurrence(self):
        for occurrence in self.eventoccurrence_set.all():
            if occurrence.state == EventOrOccurrenceState.CLOSED:
                return True
        return False

    def duplicate(self):
        event = OneTimeEvent(
            name=f"{self.name} duplikát",
            description=self.description,
            location=self.location,
            date_start=self.date_start,
            date_end=self.date_end,
            participants_enroll_state=self.participants_enroll_state,
            capacity=self.capacity,
            min_age=self.min_age,
            max_age=self.max_age,
            group=self.group,
            default_participation_fee=self.default_participation_fee,
            category=self.category,
            state=self.state,
            training_category=self.training_category,
        )
        event.save()

        for allowed_person_type in self.allowed_person_types.all():
            event.allowed_person_types.add(allowed_person_type)

        return event


class OrganizerOccurrenceAssignment(OrganizerAssignment):
    position_assignment = models.ForeignKey(
        "events.EventPositionAssignment",
        verbose_name="Pozice události",
        on_delete=models.CASCADE,
    )
    person = models.ForeignKey(
        "persons.Person", verbose_name="Osoba", on_delete=models.CASCADE
    )
    occurrence = models.ForeignKey(
        "one_time_events.OneTimeEventOccurrence", on_delete=models.CASCADE
    )
    state = models.CharField(max_length=8, choices=OneTimeEventAttendance.choices)

    def receive_amount(self):
        if self.transaction is not None:
            return self.transaction.amount

        hours = self.occurrence.hours
        wage_hour = self.position_assignment.position.wage_hour
        person_rates = PersonHourlyRate.get_person_hourly_rates(self.person)
        category = self.occurrence.event.category

        if category in person_rates:
            salary = person_rates[category] * hours
        else:
            salary = 0

        return salary + wage_hour * hours

    @property
    def is_present(self):
        return self.state == OneTimeEventAttendance.PRESENT

    @property
    def is_missing(self):
        return self.state == OneTimeEventAttendance.MISSING

    class Meta:
        unique_together = ["person", "occurrence"]


class OneTimeEventParticipantAttendance(models.Model):
    enrollment = models.ForeignKey(
        "one_time_events.OneTimeEventParticipantEnrollment", on_delete=models.CASCADE
    )
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    occurrence = models.ForeignKey(
        "one_time_events.OneTimeEventOccurrence", on_delete=models.CASCADE
    )
    state = models.CharField(max_length=8, choices=OneTimeEventAttendance.choices)

    @property
    def is_present(self):
        return self.state == OneTimeEventAttendance.PRESENT

    @property
    def is_missing(self):
        return self.state == OneTimeEventAttendance.MISSING

    class Meta:
        unique_together = ["person", "occurrence"]


class OneTimeEventOccurrence(EventOccurrence):
    organizers = models.ManyToManyField(
        "persons.Person",
        through="one_time_events.OrganizerOccurrenceAssignment",
        related_name="organizer_occurrence_assignment_set",
    )
    participants = models.ManyToManyField(
        "persons.Person", through="one_time_events.OneTimeEventParticipantAttendance"
    )

    date = models.DateField(_("Den konání"))
    hours = models.PositiveSmallIntegerField(
        _("Počet hodin"), validators=[MinValueValidator(1), MaxValueValidator(10)]
    )

    def position_organizers(self, position_assignment):
        return self.organizeroccurrenceassignment_set.filter(
            position_assignment=position_assignment
        )

    def has_attending_organizer(self):
        return self.organizeroccurrenceassignment_set.filter(
            state=OneTimeEventAttendance.PRESENT
        ).exists()

    def has_position_free_spot(self, position_assignment):
        return (
            len(self.position_organizers(position_assignment))
            < position_assignment.count
        )

    def can_enroll_position(self, person, position_assignment):
        can_possibly_enroll = super().can_enroll_position(person, position_assignment)
        if not can_possibly_enroll:
            return False
        return (
            datetime.now().date()
            + timedelta(days=settings.ORGANIZER_ENROLL_DEADLINE_DAYS)
            <= self.event.date_start
        )

    def can_unenroll_position(self, person, position_assignment):
        can_possibly_unenroll = super().can_unenroll_position(
            person, position_assignment
        )
        if not can_possibly_unenroll:
            return False
        return (
            datetime.now().date()
            + timedelta(days=settings.ORGANIZER_UNENROLL_DEADLINE_DAYS)
            <= self.event.date_start
        )

    def attending_participants_attendance(self):
        return self.onetimeeventparticipantattendance_set.filter(
            state=OneTimeEventAttendance.PRESENT
        )

    def participants_assignment_by_Q(self, q_condition):
        return self.onetimeeventparticipantattendance_set.filter(q_condition)

    def approved_participant_assignments(self):
        return self.participants_assignment_by_Q(Q()).order_by("person")

    def approved_organizer_assignment(self):
        return self.organizers_assignments_by_Q(Q())

    def missing_participants_assignments_sorted(self):
        return self.participants_assignment_by_Q(
            Q(state=OneTimeEventAttendance.MISSING)
        ).order_by("person")

    def organizers_assignments_by_Q(self, q_condition):
        return self.organizeroccurrenceassignment_set.filter(q_condition)

    def missing_organizers_assignments_sorted(self):
        return self.organizers_assignments_by_Q(
            Q(state=OneTimeEventAttendance.MISSING)
        ).order_by("person")

    def approved_organizer_assignments(self):
        return self.organizers_assignments_by_Q(Q()).order_by("person")

    def organizer_assignments_settled(self):
        return OrganizerOccurrenceAssignment.objects.filter(
            Q(occurrence=self)
            & ~Q(transaction=None)
            & ~Q(transaction__fio_transaction=None)
        )

    def can_be_reopened(self):
        return len(self.organizer_assignments_settled()) == 0

    def can_attendance_be_filled(self):
        return datetime.now(tz=timezone.get_default_timezone()).date() >= self.date

    def not_approved_when_should(self):
        return (
            self.can_attendance_be_filled()
            and self.state == EventOrOccurrenceState.CLOSED
        )

    def duplicate(self, event):
        occurrence = OneTimeEventOccurrence(
            date=self.date, hours=self.hours, event=event, state=self.state
        )
        occurrence.save()
        return occurrence


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

    def participant_attendance(self, occurrence):
        attendance = self.onetimeeventparticipantattendance_set.filter(
            occurrence=occurrence
        )
        if attendance is not None:
            return attendance.first()
        return None

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
