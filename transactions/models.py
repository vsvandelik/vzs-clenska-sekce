from datetime import datetime

from django.db.models import (
    CASCADE,
    SET_NULL,
    CharField,
    DateField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    Model,
    OneToOneField,
    PositiveIntegerField,
    Q,
)
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _

from features.models import FeatureAssignment
from persons.models import Person
from vzs.models import DatabaseSettingsMixin, ExportableCSVMixin


class BulkTransaction(Model):
    reason = CharField(_("Popis transakce"), max_length=150)
    event = ForeignKey(
        "events.Event",
        on_delete=SET_NULL,
        null=True,
        verbose_name=_("Událost"),
        related_name="event_transactions",
    )

    def __str__(self):
        return self.reason


class Transaction(ExportableCSVMixin, Model):
    class Meta:
        permissions = [("spravce_transakci", _("Správce transakcí"))]

    amount = IntegerField(_("Suma"))
    reason = CharField(_("Popis transakce"), max_length=150)
    date_due = DateField(_("Datum splatnosti"))
    person = ForeignKey(
        Person,
        on_delete=CASCADE,
        related_name="transactions",
        verbose_name=_("Osoba"),
    )
    event = ForeignKey(
        "events.Event", on_delete=SET_NULL, null=True, verbose_name=_("Událost")
    )
    feature_assigment = OneToOneField(
        FeatureAssignment,
        on_delete=SET_NULL,
        null=True,
        verbose_name=_("Vybavení"),
    )
    bulk_transaction = ForeignKey(BulkTransaction, on_delete=SET_NULL, null=True)
    fio_transaction = ForeignKey("FioTransaction", on_delete=SET_NULL, null=True)

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


class FioTransaction(Model):
    date_settled = DateField(null=True)
    fio_id = PositiveIntegerField(unique=True)


class FioSettings(DatabaseSettingsMixin):
    last_fio_fetch_time = DateTimeField(default=make_aware(datetime(1900, 1, 1)))
