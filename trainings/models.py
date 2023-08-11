from django.db import models
from events.models import (
    Event,
    EventOrOccurrenceState,
    EventOccurrence,
    TrainingCategory,
    ParticipantEnrollment,
)
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from events.utils import days_shortcut_list


class Training(Event):
    enrolled_participants = models.ManyToManyField(
        "persons.Person",
        through="trainings.TrainingParticipantEnrollment",
        related_name="enrolled_participants_set",
    )

    main_coach = models.ForeignKey(
        "persons.Person", null=True, on_delete=models.SET_NULL
    )
    category = models.CharField(
        _("Druh události"), max_length=10, choices=TrainingCategory.choices
    )

    po_from = models.TimeField(_("Od"), null=True, blank=True)
    po_to = models.TimeField(_("Do"), null=True, blank=True)

    ut_from = models.TimeField(_("Od"), null=True, blank=True)
    ut_to = models.TimeField(_("Do"), null=True, blank=True)

    st_from = models.TimeField(_("Od"), null=True, blank=True)
    st_to = models.TimeField(_("Do"), null=True, blank=True)

    ct_from = models.TimeField(_("Od"), null=True, blank=True)
    ct_to = models.TimeField(_("Do"), null=True, blank=True)

    pa_from = models.TimeField(_("Od"), null=True, blank=True)
    pa_to = models.TimeField(_("Do"), null=True, blank=True)

    so_from = models.TimeField(_("Od"), null=True, blank=True)
    so_to = models.TimeField(_("Do"), null=True, blank=True)

    ne_from = models.TimeField(_("Od"), null=True, blank=True)
    ne_to = models.TimeField(_("Do"), null=True, blank=True)

    def can_be_replaced_by(self, training):
        pass  # TODO

    def replaces_training_list(self):
        pass  # TODO

    def sorted_occurrences_list(self):
        occurrences = EventOccurrence.objects.filter(
            Q(event=self) & Q(instance_of=TrainingOccurrence)
        )
        for occurrence in occurrences:
            occurrence.datetime_start = timezone.localtime(occurrence.datetime_start)
            occurrence.datetime_end = timezone.localtime(occurrence.datetime_end)
        return occurrences

    def does_training_take_place_on_date(self, date):
        for occurrence in self.sorted_occurrences_list():
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


class TrainingReplaceability(models.Manager):
    training_1 = models.ForeignKey("events.Training", on_delete=models.CASCADE)
    training_2 = models.ForeignKey("events.Training", on_delete=models.CASCADE)

    symmetric = models.BooleanField(default=True)
    # if false -> training_1 can replace training_2 but not vice-versa
    # if true -> training_1 can replace training_2 and vice-versa

    class Meta:
        unique_together = ["training_1", "training_2"]


class TrainingOccurrence(EventOccurrence):
    datetime_start = models.DateTimeField(_("Začíná"))
    datetime_end = models.DateTimeField(_("Končí"))
    state = models.CharField(max_length=10, choices=EventOrOccurrenceState.choices)


class TrainingParticipantEnrollment(ParticipantEnrollment):
    training = models.ForeignKey("trainings.Training", on_delete=models.CASCADE)
