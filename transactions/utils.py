from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, TypedDict
from zoneinfo import ZoneInfo

from django.contrib.auth.models import Permission
from django.core.mail import send_mail
from django.db.models import Q
from django.db.models.query import QuerySet
from django.template.loader import render_to_string
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _
from fiobank import FioBank

from events.models import ParticipantEnrollment
from persons.models import Person
from vzs.settings import FIO_TOKEN

from .models import FioTransaction, Transaction

_fio_client = FioBank(FIO_TOKEN)


def _send_mail_to_accountants(subject: str, body: str):
    accountant_emails = (
        Permission.objects.get(codename="spravce_transakci")
        .user_set.select_related("person__email")
        .values_list("person__email", flat=True)
    )

    send_mail(
        subject=subject,
        message=body,
        from_email=None,
        recipient_list=accountant_emails,
        fail_silently=False,
    )


def _date_prague(date_time: datetime):
    return localdate(date_time, timezone=ZoneInfo("Europe/Prague"))


def fetch_fio(date_time_start: datetime, date_time_end: datetime):
    """
    Fetches transactions from the organisation's bank account into the DB.

    This means matching the fetched Fio transactions with the transactions in the DB.
    The matching is done by the variable symbol.

    Sends an email to the accountants if there is a problem with the matching:

    *   fetched transaction has the same VS as another previosly matched transaction
    *   fetched transaction has a different amount
        than the matched transaction from the DB
    """

    date_start = _date_prague(date_time_start)
    date_end = _date_prague(date_time_end)

    for received_transaction in _fio_client.period(date_start, date_end):
        received_variabilni = received_transaction["variable_symbol"]
        received_amount = int(received_transaction["amount"])
        received_date = received_transaction["date"]
        received_id = int(received_transaction["transaction_id"])

        if received_amount <= 0:
            # we ignore outgoing transactions
            continue

        if received_variabilni is None or received_variabilni[0] == "0":
            continue

        try:
            transaction_pk = int(received_variabilni)
        except ValueError:
            continue

        transaction = Transaction.objects.filter(pk=transaction_pk).first()

        if transaction is None:
            # received a transaction with a VS that doesn't have a matching transaction in the DB: ignore
            continue

        if transaction.fio_transaction is not None:
            fio_id = transaction.fio_transaction.fio_id
            if fio_id != received_id:
                # the account has multiple transactions with the same VS
                _send_mail_to_accountants(
                    _("Transakce se stejným VS."),
                    _(
                        "Přijatá transakce s Fio ID {0} má stejný VS jako"
                        " transakce s Fio ID {1}.\n"
                        "Transakce s Fio ID {1} je v systému registrovaná jako"
                        " transakce {2} osoby {3}.\n"
                    ).format(
                        received_id, fio_id, transaction.pk, str(transaction.person)
                    ),
                )

            # IDs match, so we just fetched the same transaction sometime in the past: ignore
            continue

        if -transaction.amount != received_amount:
            _send_mail_to_accountants(
                "Suma transakce na účtu se liší od zadané transakce v systému.",
                _(
                    "Transakce číslo {0} osoby {1} se liší v sumě"
                    "od zadané transakce v systému.\n"
                    "Zadaná suma je {2} Kč"
                    "a reálná suma je {3} Kč"
                ).format(
                    transaction.pk,
                    str(transaction.person),
                    abs(transaction.amount),
                    abs(received_amount),
                ),
            )
            continue

        fio_transaction = FioTransaction.objects.create(
            date_settled=received_date, fio_id=received_id
        )
        transaction.fio_transaction = fio_transaction
        transaction.save()


class TransactionFilterDict(TypedDict):
    """
    The type of the dictionary
    that is used by :func:`parse_transactions_filter_queryset`.
    """

    person_name: str | None
    reason: str | None
    transaction_type: str | None
    is_settled: bool | None
    amount_from: int | None
    amount_to: int | None
    date_due_from: date | None
    date_due_to: date | None
    bulk_transaction: int | None


def parse_transactions_filter_queryset(
    data: TransactionFilterDict, transactions: QuerySet[Transaction]
):
    """
    Filters ``transactions`` queryset according to the ``data`` dictionary.

    The ``data`` dictionary can come for example from a form's cleaned data
    or query parameters.

    The filter predicates are combined with logical AND.
    If a key is not present,
    the corresponding filter predicate is not applied (true for all instances).
    """

    person_name = data.get("person_name")
    reason = data.get("reason")
    transaction_type = data.get("transaction_type")
    is_settled = data.get("is_settled")
    amount_from = data.get("amount_from")
    amount_to = data.get("amount_to")
    date_due_from = data.get("date_due_from")
    date_due_to = data.get("date_due_to")
    bulk_transaction = data.get("bulk_transaction")

    if person_name is not None:
        transactions = transactions.filter(
            Q(person__first_name__icontains=person_name)
            | Q(person__last_name__icontains=person_name)
        )

    if reason is not None:
        transactions = transactions.filter(reason__icontains=reason)

    if transaction_type is not None:
        query_expression = (
            Transaction.Q_reward if transaction_type == "reward" else Transaction.Q_debt
        )
        transactions = transactions.filter(query_expression)

    if is_settled is not None:
        transactions = transactions.filter(fio_transaction__isnull=not is_settled)

    if amount_from is not None:
        transactions = transactions.filter(
            Q(amount__gte=amount_from) | Q(amount__lte=-amount_from)
        )

    if amount_to is not None:
        transactions = transactions.filter(
            Q(amount__lte=amount_to) & Q(amount__gte=-amount_to)
        )

    if date_due_from is not None:
        transactions = transactions.filter(date_due__gte=date_due_from)

    if date_due_to is not None:
        transactions = transactions.filter(date_due__lte=date_due_to)

    if bulk_transaction is not None:
        transactions = transactions.filter(bulk_transaction=bulk_transaction)

    return transactions


def send_email_transactions(transactions: Iterable[Transaction]):
    """
    Sends an email with information about each transaction in ``transactions``.
    """

    for transaction in transactions:
        html_message = render_to_string(
            "transactions/email.html", {"transaction": transaction}
        )
        send_mail(
            subject="Informace o transakci",
            message="",
            from_email=None,
            recipient_list=[transaction.person.email],
            fail_silently=False,
            html_message=html_message,
        )


@dataclass
class TransactionInfo:
    """
    A dataclass used by bulk transaction creating forms
    and views to store intermediate data.

    See :class:`transactions.views.TransactionCreateSameAmountBulkConfirmView`,
    :class:`transactions.views.TransactionCreateTrainingBulkConfirmView`
    and :class:`transactions.forms.TransactionCreateBulkConfirmForm`.
    """

    person: Person
    amount: int
    date_due: date
    enrollment: ParticipantEnrollment | None = None

    def get_amount_field_name(self):
        return f"transactions-{self.person.pk}-amount"

    def get_date_due_field_name(self):
        return f"transactions-{self.person.pk}-date_due"
