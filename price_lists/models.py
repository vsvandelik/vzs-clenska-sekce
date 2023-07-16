from django.db import models
from features.models import Feature
from django.utils.translation import gettext_lazy as _


class PriceList(models.Model):
    name = models.CharField(_("Název"), max_length=50)
    salary_base = models.PositiveIntegerField(_("Základní výplata"))
    bonuses = models.ManyToManyField(Feature, through="price_lists.PriceListBonus")

    def __str__(self):
        return self.name


class PriceListBonus(models.Model):
    price_list = models.ForeignKey("price_lists.PriceList", on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    bonus = models.PositiveIntegerField()

    class Meta:
        unique_together = ["price_list", "feature"]
