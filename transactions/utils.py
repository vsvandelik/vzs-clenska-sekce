import zoneinfo

from django.contrib.auth.models import Permission
from django.core.mail import send_mail
from django.utils import timezone
from fiobank import FioBank

from vzs import settings
from .models import Transaction, FioTransaction

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
