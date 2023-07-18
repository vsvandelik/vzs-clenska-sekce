from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from features.models import Feature
from persons.models import Person
from django.utils.translation import gettext_lazy as _


class EventPosition(models.Model):
    name = models.CharField(_("Název"), max_length=50)
    required_features = models.ManyToManyField(Feature)
    min_age_enabled = models.BooleanField(default=False)
    max_age_enabled = models.BooleanField(default=False)
    min_age = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(99)]
    )
    max_age = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(99)]
    )
    group_membership_required = models.BooleanField(default=False)
    group = models.ForeignKey("groups.Group", null=True, on_delete=models.SET_NULL)
    allowed_person_types = models.ManyToManyField("positions.PersonType")

    def required_qualifications(self):
        return self.required_features.filter(feature_type=Feature.Type.QUALIFICATION)

    def required_permissions(self):
        return self.required_features.filter(feature_type=Feature.Type.PERMISSION)

    def required_equipment(self):
        return self.required_features.filter(feature_type=Feature.Type.EQUIPMENT)

    def __str__(self):
        return self.name


class PersonType(models.Model):
    person_type = models.CharField(
        _("Typ osoby"), unique=True, max_length=10, choices=Person.Type.choices
    )

    def __str__(self):
        return self.get_person_type_display()
