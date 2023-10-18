from collections import defaultdict
from datetime import datetime, timedelta
from itertools import chain as iter_chain

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.models import (
    Event,
    EventOccurrence,
    OrganizerAssignment,
    ParticipantEnrollment,
    EventOrOccurrenceState,
)
from positions.models import EventPosition
from trainings.utils import days_shortcut_list, weekday_2_day_shortcut, weekday_pretty
from vzs import settings


class TrainingAttendance(models.TextChoices):
    PRESENT = "prezence", _("prezence")
    EXCUSED = "omluven", _("omluven")
    UNEXCUSED = "neomluven", _("neomluven")


class TrainingReplaceabilityForParticipants(models.Model):
    training_1 = models.ForeignKey(
        "trainings.Training",
        on_delete=models.CASCADE,
        related_name="replaceable_training_1",
    )
    training_2 = models.ForeignKey(
        "trainings.Training",
        on_delete=models.CASCADE,
        related_name="replaceable_training_2",
    )

    class Meta:
        unique_together = ["training_1", "training_2"]


class Training(Event):
    class Category(models.TextChoices):
        CLIMBING = "lezecky", _("lezecký")
        SWIMMING = "plavecky", _("plavecký")
        MEDICAL = "zdravoveda", _("zdravověda")

    class Meta:
        permissions = [
            ("lezecky", _("Správce lezeckých tréninků")),
            ("plavecky", _("Správce plaveckých tréninků")),
            ("zdravoveda", _("Správce zdravovědy")),
        ]

    enrolled_participants = models.ManyToManyField(
        "persons.Person",
        through="trainings.TrainingParticipantEnrollment",
        related_name="training_participant_enrollment_set",
    )

    coaches = models.ManyToManyField(
        "persons.Person",
        through="trainings.CoachPositionAssignment",
        related_name="training_coach_position_assignment_set",
    )

    main_coach_assignment = models.ForeignKey(
        "trainings.CoachPositionAssignment",
        null=True,
        on_delete=models.SET_NULL,
        related_name="main_coach_assignment",
    )

    category = models.CharField(
        _("Druh události"), max_length=10, choices=Category.choices
    )

    po_from = models.TimeField(_("Od*"), null=True, blank=True)
    po_to = models.TimeField(_("Do*"), null=True, blank=True)

    ut_from = models.TimeField(_("Od*"), null=True, blank=True)
    ut_to = models.TimeField(_("Do*"), null=True, blank=True)

    st_from = models.TimeField(_("Od*"), null=True, blank=True)
    st_to = models.TimeField(_("Do*"), null=True, blank=True)

    ct_from = models.TimeField(_("Od*"), null=True, blank=True)
    ct_to = models.TimeField(_("Do*"), null=True, blank=True)

    pa_from = models.TimeField(_("Od*"), null=True, blank=True)
    pa_to = models.TimeField(_("Do*"), null=True, blank=True)

    so_from = models.TimeField(_("Od*"), null=True, blank=True)
    so_to = models.TimeField(_("Do*"), null=True, blank=True)

    ne_from = models.TimeField(_("Od*"), null=True, blank=True)
    ne_to = models.TimeField(_("Do*"), null=True, blank=True)

    def weekly_occurs_count(self):
        return len(self.weekdays_list())

    def weekdays_list(self):
        days = days_shortcut_list()
        output = []
        for i in range(0, len(days)):
            if getattr(self, f"{days[i]}_from") is not None:
                output.append(i)
        return output

    def free_weekdays_list(self):
        return [
            weekday
            for weekday in self.weekdays_list()
            if self.has_weekday_free_spot(weekday)
        ]

    def weekdays_shortcut_list(self):
        return map(weekday_2_day_shortcut, self.weekdays_list())

    def weekdays_pretty_list(self):
        return map(weekday_pretty, self.weekdays_list())

    def can_be_replaced_by(self, training):
        replaceability = TrainingReplaceabilityForParticipants.objects.filter(
            training_1=self, training_2=training
        ).first()
        if replaceability is None:
            return False
        return True

    def replaces_training_list(self):
        replaceability = TrainingReplaceabilityForParticipants.objects.filter(
            training_1=self
        ).all()
        trainings_list = []
        for obj in replaceability:
            trainings_list.append(obj.training_2)
        return trainings_list

    def has_free_spot(self):
        if not any(map(self.has_weekday_free_spot, self.weekdays_list())):
            return False
        return True

    def can_participant_unenroll(self, person):
        if not super().can_participant_unenroll(person):
            return False

        enrollment = self.get_participant_enrollment(person)
        for transaction in enrollment.transactions.all():
            if transaction.is_settled:
                return False

        return True

    def get_participant_enrollment(self, person):
        if person is None:
            return None
        try:
            return person.trainingparticipantenrollment_set.get(training=self)
        except TrainingParticipantEnrollment.DoesNotExist:
            return None

    def enrollments_by_Q_weekday(self, condition, weekday):
        return self.trainingparticipantenrollment_set.filter(
            condition & Q(weekdays__weekday=weekday)
        )

    def enrollments_by_Q(self, condition):
        return self.trainingparticipantenrollment_set.filter(condition)

    def approved_enrollments_by_weekday(self, weekday):
        return self.enrollments_by_Q_weekday(
            Q(state=ParticipantEnrollment.State.APPROVED), weekday
        )

    def substitute_enrollments_by_weekday(self, weekday):
        return self.enrollments_by_Q_weekday(
            Q(state=ParticipantEnrollment.State.SUBSTITUTE), weekday
        )

    def all_possible_enrollments_by_weekday(self, weekday):
        return self.enrollments_by_Q_weekday(
            Q(state=ParticipantEnrollment.State.APPROVED)
            | Q(state=ParticipantEnrollment.State.SUBSTITUTE),
            weekday,
        )

    def has_weekday_free_spot(self, weekday):
        possibly_free = super().has_free_spot()
        if not possibly_free:
            if self.participants_enroll_state == ParticipantEnrollment.State.APPROVED:
                enrollments_length = self.approved_enrollments_by_weekday(
                    weekday
                ).count()
            elif (
                self.participants_enroll_state == ParticipantEnrollment.State.SUBSTITUTE
            ):
                enrollments_length = self.all_possible_enrollments_by_weekday(
                    weekday
                ).count()
            else:
                raise NotImplementedError
            return enrollments_length < self.capacity
        return True

    def _occurrences_list(self):
        return TrainingOccurrence.objects.filter(event=self)

    def _occurrences_conv_localtime(self, occurrences):
        for occurrence in occurrences:
            occurrence.datetime_start = timezone.localtime(occurrence.datetime_start)
            occurrence.datetime_end = timezone.localtime(occurrence.datetime_end)

    def occurrences_list(self):
        occurrences = self._occurrences_list()
        self._occurrences_conv_localtime(occurrences)
        return occurrences

    def sorted_occurrences_list(self):
        occurrences = self._occurrences_list().order_by("datetime_start")
        self._occurrences_conv_localtime(occurrences)
        return occurrences

    def does_training_take_place_on_date(self, date):
        for occurrence in self.occurrences_list():
            if (
                timezone.localtime(occurrence.datetime_start).date()
                <= date
                <= timezone.localtime(occurrence.datetime_end).date()
            ):
                return True
        return False

    def weekdays_occurs_list(self):
        weekdays = []
        i = 0
        for day in days_shortcut_list():
            if getattr(self, f"{day}_from") is not None:
                weekdays.append(i)
            i += 1
        return weekdays

    def organizers_assignments(self):
        return CoachOccurrenceAssignment.objects.filter(
            position__in=self.positions.all()
        )

    def position_coaches(self, position_assignment):
        return self.coachpositionassignment_set.filter(
            position_assignment=position_assignment
        )

    def __str__(self):
        return self.name

    @staticmethod
    def does_person_attends_training_of_category(person, category):
        return person.trainingparticipantenrollment_set.filter(
            training__category=category, state=ParticipantEnrollment.State.APPROVED
        )

    def substitute_enrollments_2_capacity(self):
        enrollments = self.substitute_enrollments().order_by("created_datetime")
        if self.capacity is None:
            return enrollments

        enrolled_count = {}
        for weekday in self.weekdays_list():
            enrolled_count[weekday] = len(self.approved_enrollments_by_weekday(weekday))

        chosen_count = defaultdict(lambda: 0)
        chosen_enrollments = []
        for enrollment in enrollments:
            fullness_vec = [
                enrolled_count[w.weekday] for w in enrollment.weekdays.all()
            ]
            chosen_vec = [chosen_count[w.weekday] for w in enrollment.weekdays.all()]
            if [x + y for x, y in zip(fullness_vec, chosen_vec)] < [
                self.capacity
            ] * len(fullness_vec):
                chosen_enrollments.append(enrollment)
                for w in enrollment.weekdays.all():
                    chosen_count[w.weekday] += 1

        return chosen_enrollments

    def _can_person_interact_with_nonrecursive(self, person):
        return any(
            occurence.can_person_interact_with(person)
            for occurence in self._occurrences_list()
        )

    def can_person_interact_with(self, person):
        return any(
            training._can_person_interact_with_nonrecursive(person)
            for training in iter_chain(self.replaces_training_list(), [self])
        )


class CoachPositionAssignment(models.Model):
    person = models.ForeignKey(
        "persons.Person", verbose_name="Osoba", on_delete=models.CASCADE
    )
    training = models.ForeignKey("trainings.Training", on_delete=models.CASCADE)
    position_assignment = models.ForeignKey(
        "events.EventPositionAssignment",
        verbose_name="Pozice události",
        on_delete=models.CASCADE,
    )

    def coach_attendance(self, occurrence):
        out = CoachOccurrenceAssignment.objects.filter(
            person=self.person, occurrence=occurrence
        )
        if out is None:
            return None
        return out.first()

    class Meta:
        unique_together = ["person", "training"]


class CoachOccurrenceAssignment(OrganizerAssignment):
    position_assignment = models.ForeignKey(
        "events.EventPositionAssignment",
        verbose_name="Pozice události",
        on_delete=models.CASCADE,
    )
    person = models.ForeignKey(
        "persons.Person", verbose_name="Osoba", on_delete=models.CASCADE
    )
    occurrence = models.ForeignKey(
        "trainings.TrainingOccurrence", on_delete=models.CASCADE
    )
    state = models.CharField(max_length=9, choices=TrainingAttendance.choices)

    def is_present(self):
        return self.state == TrainingAttendance.PRESENT

    def is_excused(self):
        return self.state == TrainingAttendance.EXCUSED

    def is_unexcused(self):
        return self.state == TrainingAttendance.UNEXCUSED

    class Meta:
        unique_together = ["person", "occurrence"]


class TrainingOccurrence(EventOccurrence):
    datetime_start = models.DateTimeField(_("Začíná"))
    datetime_end = models.DateTimeField(_("Končí"))

    coaches = models.ManyToManyField(
        "persons.Person",
        through="trainings.CoachOccurrenceAssignment",
        related_name="coaches_occurrence_assignment_set",
    )

    participants = models.ManyToManyField(
        "persons.Person",
        through="trainings.TrainingParticipantAttendance",
        related_name="training_participants_attendance_set",
    )

    def position_organizers(self, position_assignment):
        return self.coachoccurrenceassignment_set.filter(
            position_assignment=position_assignment
        )

    def position_organizers_attending(self, position_assignment):
        return self.coachoccurrenceassignment_set.filter(
            position_assignment=position_assignment, state=TrainingAttendance.PRESENT
        )

    def has_position_free_spot(self, position_assignment):
        return (
            len(self.position_organizers_attending(position_assignment))
            < position_assignment.count
        )

    def can_enroll_position(self, person, position_assignment):
        can_possibly_enroll = super().can_enroll_position(person, position_assignment)
        if not can_possibly_enroll:
            return False
        return (
            datetime.now(tz=timezone.get_default_timezone())
            + timedelta(days=settings.ORGANIZER_ENROLL_DEADLINE_DAYS)
            <= self.datetime_start
        )

    def can_unenroll_position(self, person, position_assignment):
        can_possibly_unenroll = super().can_unenroll_position(
            person, position_assignment
        )
        if not can_possibly_unenroll:
            return False
        return (
            not self.event.coaches.contains(person)
            and datetime.now(tz=timezone.get_default_timezone())
            + timedelta(days=settings.ORGANIZER_UNENROLL_DEADLINE_DAYS)
            <= self.datetime_start
        )

    def attending_participants_attendance(self):
        return self.trainingparticipantattendance_set.filter(
            state=TrainingAttendance.PRESENT
        )

    def has_free_participant_spot(self):
        if self.event.capacity is None:
            return True
        return len(self.attending_participants_attendance()) < self.event.capacity

    def weekday(self):
        return self.datetime_start.weekday()

    def can_coach_excuse(self, person):
        assignment = self.coachoccurrenceassignment_set.filter(
            occurrence=self, person=person
        ).first()
        if assignment is None:
            return False
        return (
            self.event.coaches.contains(person)
            and assignment.state == TrainingAttendance.PRESENT
            and datetime.now(tz=timezone.get_default_timezone())
            + timedelta(days=settings.ORGANIZER_EXCUSE_DEADLINE_DAYS)
            <= self.datetime_start
        )

    def coaches_assignments_by_Q(self, q_condition):
        return self.coachoccurrenceassignment_set.filter(q_condition)

    def excused_coaches_assignments_sorted(self):
        return self.coaches_assignments_by_Q(
            Q(state=TrainingAttendance.EXCUSED)
        ).order_by("person")

    def regular_present_coaches_assignments_sorted(self):
        return self.coaches_assignments_by_Q(
            Q(state=TrainingAttendance.PRESENT, person__in=self.event.coaches.all())
        ).order_by("person")

    def regular_not_excused_coaches_assignments_sorted(self):
        return self.coaches_assignments_by_Q(
            Q(person__in=self.event.coaches.all())
            & ~Q(state=TrainingAttendance.EXCUSED)
        ).order_by("person")

    def one_time_present_coaches_assignments_sorted(self):
        return self.coaches_assignments_by_Q(
            Q(state=TrainingAttendance.PRESENT)
            & ~Q(person__in=self.event.coaches.all())
        ).order_by("person")

    def one_time_not_excused_coaches_assignments_sorted(self):
        return self.coaches_assignments_by_Q(
            ~Q(state=TrainingAttendance.EXCUSED)
            & ~Q(person__in=self.event.coaches.all())
        ).order_by("person")

    def unexcused_coaches_assignments_sorted(self):
        return self.coaches_assignments_by_Q(
            Q(state=TrainingAttendance.UNEXCUSED)
        ).order_by("person")

    def position_present_coaches_assignments(self, position_assignment):
        return self.coaches_assignments_by_Q(
            Q(state=TrainingAttendance.PRESENT, position_assignment=position_assignment)
        )

    def participants_assignment_by_Q(self, q_condition):
        return self.trainingparticipantattendance_set.filter(q_condition)

    def regular_present_participants_assignments_sorted(self):
        return self.participants_assignment_by_Q(
            Q(
                state=TrainingAttendance.PRESENT,
                person__in=self.event.enrolled_participants.all(),
            )
        ).order_by("person")

    def regular_not_excused_participants_assignments_sorted(self):
        return self.participants_assignment_by_Q(
            Q(person__in=self.event.enrolled_participants.all())
            & ~Q(state=TrainingAttendance.EXCUSED)
        ).order_by("person")

    def one_time_present_participants_assignments_sorted(self):
        return self.participants_assignment_by_Q(
            Q(state=TrainingAttendance.PRESENT)
            & ~Q(person__in=self.event.enrolled_participants.all())
        ).order_by("person")

    def one_time_not_excused_participants_assignments_sorted(self):
        return self.participants_assignment_by_Q(
            ~Q(state=TrainingAttendance.EXCUSED)
            & ~Q(person__in=self.event.enrolled_participants.all())
        ).order_by("person")

    def excused_participants_assignments_sorted(self):
        return self.participants_assignment_by_Q(
            Q(state=TrainingAttendance.EXCUSED)
        ).order_by("person")

    def unexcused_participants_assignments_sorted(self):
        return self.participants_assignment_by_Q(
            Q(state=TrainingAttendance.UNEXCUSED)
        ).order_by("person")

    def get_participant_attendance(self, person):
        return self.trainingparticipantattendance_set.filter(
            occurrence=self, person=person
        ).first()

    def can_participant_excuse(self, person):
        participant_attendance = self.get_participant_attendance(person)
        if participant_attendance is None:
            return False
        return (
            self.event.enrolled_participants.contains(person)
            and participant_attendance.state == TrainingAttendance.PRESENT
            and datetime.now(tz=timezone.get_default_timezone())
            + timedelta(days=settings.PARTICIPANT_EXCUSE_DEADLINE_DAYS)
            <= self.datetime_start
        )

    def can_participant_unenroll(self, person):
        participant_attendance = self.get_participant_attendance(person)
        if participant_attendance is None:
            return False
        return (
            not self.event.enrolled_participants.contains(person)
            and participant_attendance.state == TrainingAttendance.PRESENT
            and datetime.now(tz=timezone.get_default_timezone())
            + timedelta(days=settings.PARTICIPANT_UNENROLL_DEADLINE_DAYS)
            <= self.datetime_start
        )

    def can_attendance_by_replaced_by(self, occurrence):
        if not self.event.can_be_replaced_by(occurrence.event):
            return False
        if self.datetime_start > occurrence.datetime_start:
            return False
        return True

    def can_participant_enroll(self, person):
        no_free_spot_for_participant = not self.has_free_participant_spot()
        is_attending_occurrence = self.get_participant_attendance(person) is not None
        is_regular_participant = person in self.event.enrolled_participants.all()
        is_past_deadline = (
            datetime.now(tz=timezone.get_default_timezone())
            + timedelta(days=settings.PARTICIPANT_ENROLL_DEADLINE_DAYS)
            > self.datetime_start
        )

        if (
            no_free_spot_for_participant
            or is_attending_occurrence
            or is_regular_participant
            or is_past_deadline
        ):
            return False

        observed = TrainingParticipantAttendance.objects.filter(
            person=person,
            # occurrence__state=EventOrOccurrenceState.COMPLETED,
            occurrence__datetime_start__lt=self.datetime_start,
        )

        excused = observed.filter(state=TrainingAttendance.EXCUSED)
        one_time_attendances = observed.filter(enrollment=None)
        if excused.count() <= one_time_attendances.count():
            return False

        for i in range(one_time_attendances.count(), excused.count()):
            if excused[i].occurrence.can_attendance_by_replaced_by(self):
                return True
        return False

    def can_attendance_be_filled(self):
        return datetime.now(tz=timezone.get_default_timezone()) > self.datetime_start

    def coach_assignments_settled(self):
        return CoachOccurrenceAssignment.objects.filter(
            Q(occurrence=self)
            & ~Q(transaction=None)
            & ~Q(transaction__fio_transaction=None)
        )

    def can_be_reopened(self):
        return len(self.coach_assignments_settled()) == 0

    @property
    def hours(self):
        td = self.datetime_end - self.datetime_start
        return td.seconds / 3600

    def can_person_interact_with(self, person):
        return (
            self.can_participant_enroll(person)
            or self.can_participant_unenroll(person)
            or self.can_participant_excuse(person)
            or self.can_coach_excuse(person)
        )


class TrainingParticipantAttendance(models.Model):
    enrollment = models.ForeignKey(
        "trainings.TrainingParticipantEnrollment", null=True, on_delete=models.CASCADE
    )
    person = models.ForeignKey(
        "persons.Person", verbose_name="Osoba", on_delete=models.CASCADE
    )
    occurrence = models.ForeignKey(
        "trainings.TrainingOccurrence", on_delete=models.CASCADE
    )
    state = models.CharField(max_length=9, choices=TrainingAttendance.choices)

    def can_unenroll(self):
        return self.occurrence.can_participant_unenroll(self.person)

    @property
    def is_present(self):
        return self.state == TrainingAttendance.PRESENT

    @property
    def is_excused(self):
        return self.state == TrainingAttendance.EXCUSED

    @property
    def is_unexcused(self):
        return self.state == TrainingAttendance.UNEXCUSED

    class Meta:
        unique_together = ["person", "occurrence"]


class TrainingParticipantEnrollment(ParticipantEnrollment):
    training = models.ForeignKey("trainings.Training", on_delete=models.CASCADE)
    person = models.ForeignKey(
        "persons.Person", verbose_name="Osoba", on_delete=models.CASCADE
    )
    weekdays = models.ManyToManyField(
        "trainings.TrainingWeekdays", related_name="training_weekdays_set"
    )
    transactions = models.ManyToManyField("transactions.Transaction")

    class Meta:
        unique_together = ["training", "person"]

    def attends_on_weekday(self, weekday):
        try:
            self.weekdays.get(weekday=weekday)
            return True
        except TrainingWeekdays.DoesNotExist:
            return False

    def participant_attendance(self, occurrence):
        out = self.trainingparticipantattendance_set.filter(occurrence=occurrence)
        if out is not None:
            return out.first()
        return None

    @property
    def event(self):
        return self.training

    @event.setter
    def event(self, value):
        self.training = value


class TrainingWeekdays(models.Model):
    weekday = models.PositiveSmallIntegerField(
        unique=True, validators=[MinValueValidator(0), MaxValueValidator(6)]
    )

    @staticmethod
    def get_or_create(weekday):
        return TrainingWeekdays.objects.get_or_create(
            weekday=weekday, defaults={"weekday": weekday}
        )[0]
