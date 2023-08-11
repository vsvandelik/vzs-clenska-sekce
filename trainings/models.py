from django.db import models
from events.models import (
    Event,
    EventOccurrence,
    TrainingCategory,
    ParticipantEnrollment,
)
from django.utils.translation import gettext_lazy as _


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


class TrainingParticipantEnrollment(ParticipantEnrollment):
    training = models.ForeignKey("trainings.Training", on_delete=models.CASCADE)
