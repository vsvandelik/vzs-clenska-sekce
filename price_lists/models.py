from django.db import models
from features.models import Feature
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


class PriceListTemplatesManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_template=True)


class PriceListNonTemplatesManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_template=False)


class PriceList(models.Model):
    objects = models.Manager()
    templates = PriceListTemplatesManager()
    nontemplates = PriceListNonTemplatesManager()

    name = models.CharField(_("Název"), max_length=50)
    salary_base = models.PositiveIntegerField(_("Základní výplata organizátorů"))
    participant_fee = models.PositiveIntegerField(_("Poplatek za účast"))
    bonus_features = models.ManyToManyField(
        Feature, through="price_lists.PriceListBonus"
    )
    is_template = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class PriceListBonus(models.Model):
    price_list = models.ForeignKey("price_lists.PriceList", on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    extra_fee = models.PositiveIntegerField(
        _("Bonusová částka"), validators=[MinValueValidator(1)]
    )

    class Meta:
        unique_together = ["price_list", "feature"]
