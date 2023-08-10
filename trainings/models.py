from django.db import models
from events.models import Event, EventOccurrence, TrainingCategory
from django.utils.translation import gettext_lazy as _


class Training(Event):
    date_start = models.DateField(_("Začíná"), null=True)
    date_end = models.DateField(_("Končí"), null=True)

    enrolled_participants = models.ManyToManyField(
        "persons.Person", through="events.ParticipantEnrollment"
    )

    main_coach = models.ForeignKey("persons.Person", on_delete=models.SET_NULL)
    category = models.CharField(
        _("Druh události"), max_length=10, choices=TrainingCategory.choices
    )

    po_start = models.TimeField()
    po_end = models.TimeField()

    ut_start = models.TimeField()
    st_end = models.TimeField()

    ct_start = models.TimeField()
    ct_end = models.TimeField()

    pa_start = models.TimeField()
    pa_end = models.TimeField()

    so_start = models.TimeField()
    so_end = models.TimeField()

    ne_start = models.TimeField()
    ne_end = models.TimeField()

    def can_be_replace_by(self, training):
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
    datetime_start = models.DateTimeField(_("Začíná"), null=True)
    datetime_end = models.DateTimeField(_("Končí"), null=True)
