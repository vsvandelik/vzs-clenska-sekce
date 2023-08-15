from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from features.models import Feature
from persons.models import Person
from django.utils.translation import gettext_lazy as _


class EventPosition(models.Model):
    name = models.CharField(_("Název"), max_length=50)
    wage_hour = models.PositiveIntegerField(
        _("Hodinová sazba"), null=True, validators=[MinValueValidator(1)]
    )
    required_features = models.ManyToManyField(Feature)
    min_age = models.PositiveSmallIntegerField(
        _("Minimální věk"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )
    max_age = models.PositiveSmallIntegerField(
        _("Maximální věk"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )
    group = models.ForeignKey("groups.Group", null=True, on_delete=models.SET_NULL)
    allowed_person_types = models.ManyToManyField("persons.PersonType")

    def required_qualifications(self):
        return self.required_features.filter(feature_type=Feature.Type.QUALIFICATION)

    def required_permissions(self):
        return self.required_features.filter(feature_type=Feature.Type.PERMISSION)

    def required_equipment(self):
        return self.required_features.filter(feature_type=Feature.Type.EQUIPMENT)

    def __str__(self):
        return self.name
