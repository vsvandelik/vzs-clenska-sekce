from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (
    SET_NULL,
    CharField,
    ForeignKey,
    ManyToManyField,
    Model,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    Q,
)
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from events.models import Event
from events.utils import check_common_requirements
from features.models import Feature, FeatureAssignment


class EventPosition(Model):
    name = CharField(
        _("Název"),
        max_length=50,
        unique=True,
        error_messages={"unique": "Pozice s tímto názvem již existuje."},
    )
    wage_hour = PositiveIntegerField(
        _("Hodinová sazba"), validators=[MinValueValidator(1)]
    )
    required_features = ManyToManyField(Feature)
    min_age = PositiveSmallIntegerField(
        _("Minimální věk"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )
    max_age = PositiveSmallIntegerField(
        _("Maximální věk"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )
    group = ForeignKey(
        "groups.Group", verbose_name=_("Skupina"), null=True, on_delete=SET_NULL
    )
    allowed_person_types = ManyToManyField("events.EventPersonTypeConstraint")

    def required_qualifications(self):
        return self.required_features.filter(feature_type=Feature.Type.QUALIFICATION)

    def required_permissions(self):
        return self.required_features.filter(feature_type=Feature.Type.PERMISSION)

    def required_equipment(self):
        return self.required_features.filter(feature_type=Feature.Type.EQUIPMENT)

    def events_using(self):
        return Event.objects.filter(positions__id__contains=self.id)

    def does_person_satisfy_requirements(self, person, date):
        if not check_common_requirements(self, person):
            return False

        features = self.required_features

        feature_type_conditions = [
            Q(feature_type=Feature.Type.QUALIFICATION),
            Q(feature_type=Feature.Type.PERMISSION),
            Q(feature_type=Feature.Type.EQUIPMENT),
        ]

        for condition in feature_type_conditions:
            observed_features = features.filter(condition)

            if observed_features.exists():
                assignment = FeatureAssignment.objects.filter(
                    Q(feature__in=observed_features)
                    & Q(person=person)
                    & Q(date_assigned__lte=date)
                    & Q(date_returned=None)
                    & (Q(date_expire=None) | Q(date_expire__gte=date))
                ).first()

                if assignment is None:
                    return False

        return True

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("positions:detail", args=[self.pk])
