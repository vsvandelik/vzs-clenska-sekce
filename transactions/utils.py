from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Annotated, TypedDict
from zoneinfo import ZoneInfo

from django.core.mail import send_mail
from django.db.models import Q, Sum
from django.template.loader import render_to_string
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _
from fiobank import FioBank

from events.models import ParticipantEnrollment
from persons.models import Person
from users.utils import get_permission_by_codename
from vzs.settings import FIO_TOKEN, ICO
from vzs.utils import (
    email_notification_recipient_set,
    get_csv_writer_http_response,
    get_xml_http_response,
    now,
)
from .models import FioTransaction, Transaction, BulkTransaction

_fio_client = FioBank(FIO_TOKEN)


def _send_mail_to_accountants(subject: str, body: str):
    accountant_emails = (
        get_permission_by_codename("transakce")
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


class TransactionFilter(TypedDict, total=False):
    """
    Defines a filter for transactions.

    Use with :func:`vzs.utils.filter_queryset`.
    """

    person_name: Annotated[
        str,
        lambda person_name: Q(person__first_name__icontains=person_name)
        | Q(person__last_name__icontains=person_name),
    ]

    reason: Annotated[str, lambda reason: Q(reason__icontains=reason)]

    transaction_type: Annotated[
        str,
        lambda transaction_type: (
            Transaction.Q_reward if transaction_type == "reward" else Transaction.Q_debt
        ),
    ]

    is_settled: Annotated[
        str,
        lambda is_settled: Q(fio_transaction__isnull=is_settled != "paid"),
    ]

    amount_from: Annotated[
        int,
        lambda amount_from: Q(amount__gte=amount_from) | Q(amount__lte=-amount_from),
    ]

    amount_to: Annotated[
        int, lambda amount_to: Q(amount__lte=amount_to) & Q(amount__gte=-amount_to)
    ]

    date_due_from: Annotated[date, lambda date_due_from: Q(date_due__gte=date_due_from)]

    date_due_to: Annotated[date, lambda date_due_to: Q(date_due__lte=date_due_to)]

    bulk_transaction: Annotated[
        BulkTransaction, lambda bulk_transaction: Q(bulk_transaction=bulk_transaction)
    ]


def send_email_transactions(transactions: Iterable[Transaction]):
    """
    Sends an email with information about each transaction in ``transactions``.
    """

    for transaction in transactions:
        html_message = render_to_string(
            "transactions/email.html", {"transaction": transaction}
        )
        emails = email_notification_recipient_set(transaction.person)
        send_mail(
            subject="Informace o transakci",
            message="",
            from_email=None,
            recipient_list=emails,
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


def export_rewards_to_csv(year, month):
    writer, http_response = get_csv_writer_http_response(f"vyplaty-{year}-{month}")

    persons_summaries = (
        Person.objects.filter(
            transactions__date_due__year=year,
            transactions__date_due__month=month,
            transactions__amount__gt=0,
        )
        .distinct()
        .annotate(amount_sum=Sum("transactions__amount"))
        .order_by("last_name", "first_name")
    )

    for person in persons_summaries:
        divided_rewards = {}

        hourly_rates = {h.event_type: h.hourly_rate for h in person.hourly_rates.all()}
        person_rewards = person.transactions.filter(
            date_due__year=year,
            date_due__month=month,
            amount__gt=0,
            event__isnull=False,
        )

        for reward in person_rewards:
            category = (
                reward.event.category
                if reward.event.category in hourly_rates
                else "nezarazeno"
            )
            divided_rewards.setdefault(category, 0)
            divided_rewards[category] += reward.amount

        writer.writerow(
            [person.last_name, person.first_name, "", "", person.amount_sum]
        )

        for category, amount in divided_rewards.items():
            writer.writerow(["", "", category, hourly_rates.get(category, ""), amount])

    return http_response


def export_debts_to_xml(year, month):
    http_response = get_xml_http_response(f"faktury-{year}-{month}")

    transactions = Transaction.objects.filter(
        date_due__year=year, date_due__month=month, amount__lt=0
    )

    data = {"transactions": transactions, "ico": ICO, "id": now().timestamp()}

    text_content = render_to_string("transactions_xml/invoices.xml", context=data)
    http_response.write(text_content.encode("utf8"))

    return http_response
