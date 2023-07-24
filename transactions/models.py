from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.models import Event
from features.models import FeatureAssignment
from persons.models import Person
from vzs import models as vzs_models


class Transaction(vzs_models.ExportableCSVMixin, models.Model):
    class Meta:
        permissions = [("spravce_transakci", _("Správce transakcí"))]

    amount = models.IntegerField(_("Suma"))
    reason = models.CharField(_("Popis transakce"), max_length=150)
    date_due = models.DateField(_("Datum splatnosti"))
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("Osoba"),
    )
    event = models.ForeignKey(
        Event, on_delete=models.SET_NULL, null=True, verbose_name=_("Událost")
    )
    feature_assigment = models.OneToOneField(
        FeatureAssignment,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Vybavení"),
    )
    fio_transaction = models.ForeignKey(
        "FioTransaction", on_delete=models.SET_NULL, null=True
    )

    Q_debt = Q(amount__lt=0)
    Q_reward = Q(amount__gt=0)

    csv_order = [
        "person",
        "event",
        "feature_assigment",
        "amount",
        "type",
        "reason",
        "date_due",
    ]
    csv_labels = {"type": "Druh transakce"}
    csv_getters = {
        "amount": lambda instance: abs(instance.amount),
        "type": lambda instance: instance.reward_string,
    }

    @property
    def is_settled(self):
        return self.fio_transaction is not None

    @property
    def is_reward(self):
        return self.amount > 0

    @property
    def reward_string(self):
        return "Odměna" if self.is_reward else "Dluh"


class FioTransaction(models.Model):
    date_settled = models.DateField(null=True)
    fio_id = models.PositiveIntegerField(unique=True)


class FioSettings(vzs_models.DatabaseSettingsMixin):
    last_fio_fetch_time = models.DateTimeField(
        default=timezone.make_aware(datetime(1900, 1, 1))
    )
