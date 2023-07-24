from .models import Transaction, FioTransaction

from vzs import settings

from django.contrib.auth.models import Permission
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Q
from django.template.loader import render_to_string

from fiobank import FioBank

import zoneinfo


_fio_client = FioBank(settings.FIO_TOKEN)


def _send_mail_to_accountants(subject, body):
    accountant_emails = (
        Permission.objects.get(codename="spravce_transakci")
        .user_set.select_related("person__email")
        .values_list("person__email", flat=True)
    )

    send_mail(
        subject,
        body,
        None,
        accountant_emails,
        fail_silently=False,
    )


def _date_prague(date):
    return timezone.localdate(date, timezone=zoneinfo.ZoneInfo("Europe/Prague"))


def fetch_fio(date_start, date_end):
    date_start = _date_prague(date_start)
    date_end = _date_prague(date_end)

    for received_transaction in _fio_client.period(date_start, date_end):
        recevied_variabilni = received_transaction["variable_symbol"]
        received_amount = int(received_transaction["amount"])
        received_date = received_transaction["date"]
        received_id = int(received_transaction["transaction_id"])

        if received_amount <= 0:
            # we ignore outgoing transactions
            continue

        if recevied_variabilni is None or recevied_variabilni[0] == "0":
            continue

        try:
            transaction_pk = int(recevied_variabilni)
        except ValueError:
            continue

        transaction = Transaction.objects.filter(pk=transaction_pk).first()

        if transaction is None:
            # received a transaction with a VS that doesn't have a matching transaction in the DB: ignore
            continue

        if transaction.fio_transaction is not None:
            if transaction.fio_transaction.fio_id != received_id:
                # the account has multiple transactions with the same VS
                _send_mail_to_accountants(
                    "Transakce se stejným VS.",
                    (
                        f"Přijatá transakce s Fio ID {received_id} má stejný VS"
                        f" jako transakce s Fio ID {transaction.fio_transaction.fio_id}.\n"
                        f"Transakce s Fio ID {transaction.fio_transaction.fio_id} je v systému registrovaná jako transakce {transaction.pk} osoby {str(transaction.person)}.\n"
                    ),
                )

            # IDs match, so we just fetched the same transaction sometime in the past: ignore
            continue

        if -transaction.amount != received_amount:
            _send_mail_to_accountants(
                "Suma transakce na účtu se liší od zadané transakce v systému.",
                (
                    f"Transakce číslo {transaction.pk} osoby {str(transaction.person)} se liší v sumě od zadané transakce v systému.\n"
                    f"Zadaná suma je {abs(transaction.amount)} Kč a reálná suma je {abs(received_amount)} Kč"
                ),
            )
            continue

        fio_transaction = FioTransaction.objects.create(
            date_settled=received_date, fio_id=received_id
        )
        transaction.fio_transaction = fio_transaction
        transaction.save()


def parse_transactions_filter_queryset(cleaned_data, transactions):
    person_name = cleaned_data.get("person_name")
    reason = cleaned_data.get("reason")
    transaction_type = cleaned_data.get("transaction_type")
    is_settled = cleaned_data.get("is_settled")
    amount_from = cleaned_data.get("amount_from")
    amount_to = cleaned_data.get("amount_to")
    date_due_from = cleaned_data.get("date_due_from")
    date_due_to = cleaned_data.get("date_due_to")

    if person_name:
        transactions = transactions.filter(
            Q(person__first_name__icontains=person_name)
            | Q(person__last_name__icontains=person_name)
        )

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

    return transactions


def send_email_transactions(transactions):
    for transaction in transactions:
        html_message = render_to_string(
            "transactions/email.html", {"transaction": transaction}
        )
        send_mail(
            "Informace o transakci",
            "",
            None,
            [transaction.person.email],
            fail_silently=False,
            html_message=html_message,
        )
