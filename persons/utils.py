from persons.models import Person, Transaction, FioTransaction

from vzs import settings

from google_integration import google_directory

from fiobank import FioBank

from django.core.mail import send_mail
from django.utils import dateparse
from django.contrib.auth.models import Permission
from django.utils import timezone

import requests
import datetime
import zoneinfo


def sync_single_group_with_google(local_group):
    google_email = local_group.google_email

    local_emails = {p.email for p in local_group.members.all()}
    google_emails = {
        m["email"] for m in google_directory.get_group_members(google_email)
    }

    if not local_group.google_as_members_authority:
        members_to_add = local_emails - google_emails
        members_to_remove = google_emails - local_emails

        for email in members_to_add:
            google_directory.add_member_to_group(email, google_email)

        for email in members_to_remove:
            google_directory.remove_member_from_group(email, google_email)

    else:
        members_to_add = google_emails - local_emails
        members_to_remove = local_emails - google_emails

        for email in members_to_add:
            try:
                local_person = Person.objects.get(email=email)
                local_group.members.add(local_person)
            except Person.DoesNotExist:
                pass

        for email in members_to_remove:
            local_group.members.remove(Person.objects.get(email=email))


_fio_client = FioBank(settings.FIO_TOKEN)
_received_transactions_filter = ["Příjem převodem uvnitř banky"]


def _send_mail_to_accountants(subject, body):
    accountant_emails = (
        Permission.objects.get(codename="ucetni")
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
        received_type = received_transaction["type"]
        recevied_variabilni = received_transaction["variable_symbol"]
        received_amount = int(received_transaction["amount"])
        received_date = received_transaction["date"]
        received_id = int(received_transaction["transaction_id"])

        if received_type not in _received_transactions_filter:
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
            print(transaction.pk, transaction.fio_transaction.fio_id, received_id)
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
                "Suma přijaté transakce se liší od zadané.",
                (
                    f"Přijatá transakce číslo {transaction.pk} zadaná osobě {str(transaction.person)} se liší v sumě od zadané transakce.\n"
                    f"Zadaná suma je {-transaction.amount} Kč a přijatá suma je {received_amount} Kč"
                ),
            )
            continue

        fio_transaction = FioTransaction.objects.create(
            date_settled=received_date, fio_id=received_id
        )
        transaction.fio_transaction = fio_transaction
        transaction.save()
