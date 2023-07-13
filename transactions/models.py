from datetime import datetime

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from events.models import Event
from features.models import FeatureAssignment
from persons.models import Person
from vzs import models as vzs_models


class Transaction(models.Model):
    class Meta:
        permissions = [("spravce_transakci", _("Správce transakcí"))]

    amount = models.IntegerField(_("Suma"))
    reason = models.CharField(_("Popis transakce"), max_length=150)
    date_due = models.DateField(_("Datum splatnosti"))
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="transactions"
    )
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True)
    feature_assigment = models.OneToOneField(
        FeatureAssignment, on_delete=models.SET_NULL, null=True
    )
    fio_transaction = models.ForeignKey(
        "FioTransaction", on_delete=models.SET_NULL, null=True
    )

    def is_settled(self):
        return self.fio_transaction is not None


class FioTransaction(models.Model):
    date_settled = models.DateField(null=True)
    fio_id = models.PositiveIntegerField(unique=True)


class FioSettings(vzs_models.DatabaseSettingsMixin):
    last_fio_fetch_time = models.DateTimeField(
        default=timezone.make_aware(datetime(1900, 1, 1))
    )
