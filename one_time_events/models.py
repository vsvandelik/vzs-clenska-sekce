from django.db import models
from events.models import Event, EventOccurrence, ParticipantEnrollment
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class OneTimeEvent(Event):
    class Category(models.TextChoices):
        COMMERCIAL = "komercni", _("komerční")
        COURSE = "kurz", _("kurz")
        PRESENTATION = "prezentacni", _("prezentační")

    enrolled_participants = models.ManyToManyField(
        "persons.Person", through="one_time_events.OneTimeEventParticipantEnrollment"
    )
    default_participation_fee = models.PositiveIntegerField(
        _("Poplatek za účast"), null=True, blank=True
    )
    category = models.CharField(
        _("Druh události"), max_length=11, choices=Category.choices
    )


class OneTimeEventOccurrence(EventOccurrence):
    date = models.DateTimeField(_("Den konání"), null=True)
    hours = models.PositiveSmallIntegerField(
        _("Počet hodin"), validators=[MinValueValidator(1), MaxValueValidator(10)]
    )


class OneTimeEventParticipantEnrollment(ParticipantEnrollment):
    one_time_event = models.ForeignKey(
        "one_time_events.OneTimeEvent", on_delete=models.CASCADE
    )
    agreed_participation_fee = models.PositiveIntegerField(_("Poplatek za účast"))
