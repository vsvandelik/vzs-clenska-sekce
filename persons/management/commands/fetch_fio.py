from persons.utils import fetch_fio

from fiobank import ThrottlingError

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from datetime import timedelta


class Command(BaseCommand):
    help = "Fetches transactions from the organisation's bank account into the DB."

    def handle(self, *args, **options):
        now = timezone.now()
        yesterday = now - timedelta(days=1)

        try:
            fetch_fio(yesterday, now)
        except ThrottlingError:
            self.stdout.write(
                self.style.ERROR(
                    _(f"Transakce je možné stahovat maximálne jednou za 30 sekund.")
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS(_(f"Úspěšně stáhnuté transakce.")))
