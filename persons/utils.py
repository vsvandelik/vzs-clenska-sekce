from persons.models import Person, Transaction

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


def _date_prague(date):
    return timezone.localdate(date, timezone=zoneinfo.ZoneInfo("Europe/Prague"))


def fetch_fio(date_start, date_end):
    date_start = _date_prague(date_start)
    date_end = _date_prague(date_end)

    for received_transaction in _fio_client.period(date_start, date_end):
        if received_transaction["type"] not in _received_transactions_filter:
            continue

        variabilni = received_transaction["variable_symbol"]

        if variabilni is None or len(variabilni) == 0 or variabilni[0] == "0":
            continue

        received_amount = int(received_transaction["amount"])
        received_date = received_transaction["date"]

        transaction_pk = int(variabilni)
        transaction = Transaction.objects.filter(pk=transaction_pk).first()

        if transaction is None:
            # TODO: decide what to do if we found a transaction of {received_amount} with VS {transaction_pk} without a DB entry
            continue

        if transaction.date_settled is not None:
            continue

        if -transaction.amount != received_amount:
            accountant_users = (
                Permission.objects.get(codename="ucetni")
                .user_set.select_related("person__email")
                .all()
            )

            send_mail(
                "Suma přijaté transakce se liší od zadané.",
                (
                    f"Přijatá transakce číslo {transaction.pk} zadaná osobě {str(transaction.person)} se liší v sumě od zadané transakce.\n"
                    f"Zadaná suma je {-transaction.amount} Kč a přijatá suma je {received_amount} Kč"
                ),
                None,
                accountant_users.values_list("person__email", flat=True),
                fail_silently=False,
            )

            continue

        transaction.date_settled = received_date
        transaction.save()
