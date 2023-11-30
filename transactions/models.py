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
    """
    Represents a bulk transaction, i.e. a collection of transactions
    that were created in a bulk.

    Used to store the information that the transactions are related.
    """

    reason = CharField(_("Popis transakce"), max_length=150)
    """
    The reason for the whole set of this bulk's sub-transactions.
    """

    event = ForeignKey(
        "events.Event",
        on_delete=SET_NULL,
        null=True,
        verbose_name=_("Událost"),
        related_name="event_transactions",
    )
    """
    The event to which the sub-transactions are related, if any.
    """

    def __str__(self):
        return self.reason


class Transaction(ExportableCSVMixin, Model):
    """
    Represents a financial transaction between the organisation and a person.

    Primary key represents the transaction variable symbol.
    """

    class Meta:
        permissions = [("spravce_transakci", _("Správce transakcí"))]

    amount = IntegerField(_("Suma"))
    """
    A negative value represents a debt, positive value represents a reward.
    """

    reason = CharField(_("Popis transakce"), max_length=150)
    """
    Textual description of the transaction reason.
    """

    date_due = DateField(_("Datum splatnosti"))
    """
    The date by which the transaction should be settled.
    """

    person = ForeignKey(
        Person,
        on_delete=CASCADE,
        related_name="transactions",
        verbose_name=_("Osoba"),
    )
    """
    Person to whom the transaction applies.
    """

    event = ForeignKey(
        "events.Event", on_delete=SET_NULL, null=True, verbose_name=_("Událost")
    )
    """
    An associated event, if the transaction is related to an event.
    """

    feature_assigment = OneToOneField(
        FeatureAssignment,
        on_delete=SET_NULL,
        null=True,
        verbose_name=_("Vybavení"),
    )
    """
    A feature assignment, if the transaction is related to a feature assignment.
    """

    bulk_transaction = ForeignKey(BulkTransaction, on_delete=SET_NULL, null=True)
    """
    A bulk transaction, if the transaction is related to a bulk transaction.
    """

    fio_transaction = ForeignKey("FioTransaction", on_delete=SET_NULL, null=True)
    """
    Fio transaction instance, if this transaction was fetched from Fio
    and therefore settled.
    """

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
        """
        Textual representation of the transaction type (debt or reward).
        """

        return "Odměna" if self.is_reward else "Dluh"


class FioTransaction(Model):
    """
    Represents a transaction from the Fio API.
    """

    date_settled = DateField(null=True)
    """
    Date when the transaction was settled.
    """

    fio_id = PositiveIntegerField(unique=True)
    """
    ID of the transaction in the Fio API.
    
    Corresponds to the ``transaction_id`` attribute key
    in the ``fiobank`` Python package.
    """


class FioSettings(DatabaseSettingsMixin):
    """
    Singleton model for information relating to Fio.
    """

    last_fio_fetch_time = DateTimeField(default=make_aware(datetime(1900, 1, 1)))
    """
    The last time Fio transactions were fetched.
    Used as a possible beginning of the period from which to fetch Fio transactions.
    """
