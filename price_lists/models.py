from django.db import models
from features.models import Feature
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


class PriceList(models.Model):
    name = models.CharField(_("Název"), max_length=50)
    salary_base = models.PositiveIntegerField(_("Základní výplata"))
    bonus_features = models.ManyToManyField(
        Feature, through="price_lists.PriceListBonus"
    )

    def __str__(self):
        return self.name


class PriceListBonus(models.Model):
    price_list = models.ForeignKey("price_lists.PriceList", on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    extra_payment = models.PositiveIntegerField(
        _("Bonusová částka"), validators=[MinValueValidator(1)]
    )

    class Meta:
        unique_together = ["price_list", "feature"]
