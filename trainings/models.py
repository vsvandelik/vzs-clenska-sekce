from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.models import (
    Event,
    EventOccurrence,
    ParticipantEnrollment,
    OrganizerPositionAssignment,
)
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

    coaches_assignment = models.ManyToManyField(
        "trainings.TrainingCoachPositionAssignment",
        related_name="training_coach_position_assignment_set",
    )
    main_coach = models.ForeignKey(
        "persons.Person", null=True, on_delete=models.SET_NULL
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
        count = 0
        for day in days_shortcut_list():
            if getattr(self, f"{day}_from") is not None:
                count += 1
        return count

    def weekdays_list(self):
        days = days_shortcut_list()
        output = []
        for i in range(0, len(days)):
            if getattr(self, f"{days[i]}_from") is not None:
                output.append(i)
        return output

    def weekdays_shortcut_list(self):
        return map(weekday_2_day_shortcut, self.weekdays_list())

    def weekdays_pretty_list(self):
        return map(weekday_pretty, self.weekdays_list())

    def can_be_replaced_by(self, training):
        pass  # TODO

    def replaces_training_list(self):
        pass  # TODO

    def can_person_enroll_as_participant(self, person):
        return True
        raise NotImplementedError

    def can_participant_unenroll(self, person):
        return True
        raise NotImplementedError

    def get_participant_enrollment(self, person):
        return True
        raise NotImplementedError

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

    def enrollments_by_state(self, state):
        output = []
        for enrolled_participant in self.enrolled_participants.all():
            enrollment = enrolled_participant.trainingparticipantenrollment_set.get(
                training=self
            )
            if enrollment.state == state:
                output.append(enrollment)
        return output

    def __str__(self):
        return self.name

    @staticmethod
    def does_person_attends_training_of_category(person, category):
        for training_enrollment in person.trainingparticipantenrollment_set.all():
            if (
                training_enrollment.state == ParticipantEnrollment.State.APPROVED
                and training_enrollment.training.category == category
            ):
                return True
        return False


class TrainingCoachPositionAssignment(OrganizerPositionAssignment):
    training = models.ForeignKey("trainings.Training", on_delete=models.CASCADE)


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


class TrainingOccurrence(EventOccurrence):
    datetime_start = models.DateTimeField(_("Začíná"))
    datetime_end = models.DateTimeField(_("Končí"))

    missing_participants_excused = models.ManyToManyField(
        "persons.Person",
        through="trainings.TrainingOccurrenceAttendanceCompensationOpportunity",
        through_fields=("training_occurrence_excused", "person"),
        related_name="training_occurrence_attendance_compensation_opportunity_set",
    )

    missing_coaches_excused = models.ManyToManyField(
        "persons.Person",
        through="trainings.TrainingOneTimeCoachPosition",
        through_fields=("training_occurrence", "coach_excused"),
        related_name="training_one_time_coach_position_set",
    )


class TrainingOccurrenceAttendanceCompensationOpportunity(models.Model):
    training_occurrence_excused = models.ForeignKey(
        "trainings.TrainingOccurrence",
        on_delete=models.CASCADE,
        related_name="training_occurrence_excused",
    )
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    attendance = models.CharField(max_length=11, choices=TrainingAttendance.choices)
    training_occurrence_substitute = models.ForeignKey(
        "trainings.TrainingOccurrence",
        null=True,
        on_delete=models.SET_NULL,
        related_name="training_occurrence_substitute",
    )
    excuse_datetime = models.DateTimeField()

    class Meta:
        unique_together = ["training_occurrence_excused", "person"]
        indexes = [models.Index(fields=["training_occurrence_substitute"])]


class TrainingOneTimeCoachPositionManager(models.Manager):
    def get_queryset(self):
        # TODO: somehow add condition that the training_occurrence is upcoming
        return self.get_queryset().filter(coach_substitute=None)


class TrainingOneTimeCoachPosition(models.Model):
    objects = models.Manager()
    free_upcoming = TrainingOneTimeCoachPositionManager()

    training_occurrence = models.ForeignKey(
        "trainings.TrainingOccurrence", on_delete=models.CASCADE
    )
    coach_excused = models.ForeignKey(
        "persons.Person", on_delete=models.CASCADE, related_name="coach_excused"
    )
    coach_substitute = models.ForeignKey(
        "persons.Person",
        null=True,
        on_delete=models.CASCADE,
        related_name="coach_substitute",
    )
    coach_substitute_attendance = models.CharField(
        max_length=11, choices=TrainingAttendance.choices
    )
    excuse_datetime = models.DateTimeField()

    class Meta:
        unique_together = ["training_occurrence", "coach_excused"]


class TrainingParticipantEnrollment(ParticipantEnrollment):
    training = models.ForeignKey("trainings.Training", on_delete=models.CASCADE)
    person = models.ForeignKey(
        "persons.Person", verbose_name="Osoba", on_delete=models.CASCADE
    )
    weekdays = models.ManyToManyField(
        "trainings.TrainingWeekdays", related_name="training_weekdays_set"
    )
    transactions = models.ManyToManyField("transactions.Transaction")

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
