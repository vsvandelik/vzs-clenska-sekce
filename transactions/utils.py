from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
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


def parse_transactions_filter_queryset(
    cleaned_data: Mapping[str, Any], transactions: QuerySet[Transaction]
):
    person_name = cleaned_data.get("person_name")
    reason = cleaned_data.get("reason")
    transaction_type = cleaned_data.get("transaction_type")
    is_settled = cleaned_data.get("is_settled")
    amount_from = cleaned_data.get("amount_from")
    amount_to = cleaned_data.get("amount_to")
    date_due_from = cleaned_data.get("date_due_from")
    date_due_to = cleaned_data.get("date_due_to")
    bulk_transaction = cleaned_data.get("bulk_transaction")

    if person_name:
        transactions = transactions.filter(
            Q(person__first_name__icontains=person_name)
            | Q(person__last_name__icontains=person_name)
        )

    if reason:
        transactions = transactions.filter(reason__icontains=reason)

    if transaction_type:
        query_expression = (
            Transaction.Q_reward if transaction_type == "reward" else Transaction.Q_debt
        )
        transactions = transactions.filter(query_expression)

    if is_settled:
        transactions = transactions.filter(fio_transaction__isnull=not is_settled)

    if amount_from:
        transactions = transactions.filter(
            Q(amount__gte=amount_from) | Q(amount__lte=-amount_from)
        )

    if amount_to:
        transactions = transactions.filter(
            Q(amount__lte=amount_to) & Q(amount__gte=-amount_to)
        )

    if date_due_from:
        transactions = transactions.filter(date_due__gte=date_due_from)

    if date_due_to:
        transactions = transactions.filter(date_due__lte=date_due_to)

    if bulk_transaction:
        transactions = transactions.filter(bulk_transaction=bulk_transaction)

    return transactions


def send_email_transactions(transactions: Iterable[Transaction]):
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
    person: Person
    amount: int
    date_due: date
    enrollment: ParticipantEnrollment | None = None

    def get_amount_field_name(self):
        return f"transactions-{self.person.pk}-amount"

    def get_date_due_field_name(self):
        return f"transactions-{self.person.pk}-date_due"
