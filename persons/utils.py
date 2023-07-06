import requests
import datetime

from google_integration import google_directory
from persons.models import Person, Transaction
from vzs import settings
from django.utils import dateparse


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


_scanned_transactions = [8]


def fetch_fio_transactions(date_start, date_end):
    result = requests.get(
        f"https://www.fio.cz/ib_api/rest/periods/{settings.FIO_TOKEN}/{date_start}/{date_end}/transactions.json"
    ).json()

    for transaction in result["accountStatement"]["transactionList"]["transaction"]:
        transaction_type = int(transaction["column8"]["id"])

        if transaction_type not in _scanned_transactions:
            continue

        column_variabilni = transaction["column5"]

        if column_variabilni is None:
            continue

        variabilni = column_variabilni["value"]

        if len(variabilni) == 0 or variabilni[0] == "0":
            continue

        amount = int(transaction["column1"]["value"])
        date_settled = datetime.datetime.strptime(
            transaction["column0"]["value"], "%Y-%m-%d%z"
        ).date()

        transaction_pk = int(variabilni)
        transaction = Transaction.objects.filter(pk=transaction_pk).first()

        if transaction is None:
            continue

        if transaction.date_settled is not None:
            continue

        if transaction.amount != amount:
            # TODO: what to do if only amounts differ?
            continue

        transaction.date_settled = date_settled
        transaction.save()
