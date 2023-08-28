from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.models import (
    Event,
    EventOccurrence,
    ParticipantEnrollment,
    OrganizerAssignment,
)
from positions.models import EventPosition
from trainings.utils import days_shortcut_list, weekday_pretty, weekday_2_day_shortcut


class TrainingAttendance(models.TextChoices):
    UNSET = "nenastaveno", _("nenastaveno")
    PRESENT = "prezence", _("prezence")
    MISSING = "absence", _("absence")


class Training(Event):
    class Category(models.TextChoices):
        CLIMBING = "lezecky", _("lezecký")
        SWIMMING = "plavecky", _("plavecký")
        MEDICAL = "zdravoveda", _("zdravověda")

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
        pass  # TODO

    def replaces_training_list(self):
        pass  # TODO

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

    def __str__(self):
        return self.name

    @staticmethod
    def does_person_attends_training_of_category(person, category):
        return person.trainingparticipantenrollment_set.filter(
            training__category=category, state=ParticipantEnrollment.State.APPROVED
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

    class Meta:
        unique_together = ["person", "training"]


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


class CoachOccurrenceAssignment(OrganizerAssignment):
    person = models.ForeignKey(
        "persons.Person", verbose_name="Osoba", on_delete=models.CASCADE
    )
    occurrence = models.ForeignKey(
        "trainings.TrainingOccurrence", on_delete=models.CASCADE
    )

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

    attending_participants = models.ManyToManyField(
        "persons.Person",
        through="trainings.TrainingParticipantAttendance",
        related_name="training_participants_attendance_set",
    )

    def weekday(self):
        return self.datetime_start.weekday()


class TrainingParticipantAttendance(models.Model):
    enrollment = models.ForeignKey(
        "trainings.TrainingParticipantEnrollment", null=True, on_delete=models.CASCADE
    )
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    occurrence = models.ForeignKey(
        "trainings.TrainingOccurrence", on_delete=models.CASCADE
    )

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
