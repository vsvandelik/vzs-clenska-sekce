from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from fiobank import ThrottlingError

from transactions.models import FioSettings
from transactions.utils import fetch_fio
from vzs.settings import CURRENT_DATETIME


class Command(BaseCommand):
    help = (
        "Fetches transactions from the organisation's bank account into the DB."
        "Can optionally specify <days> for the length of the period."
        "Otherwise fetches since the last success."
    )

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int)

    def handle(self, *args, **options):
        settings = FioSettings.load()
        now = CURRENT_DATETIME()

        days_argument = options["days"]

        begin_time = (
            now - timedelta(days=days_argument)
            if days_argument
            else settings.last_fio_fetch_time
        )

        try:
            fetch_fio(begin_time, now)
        except ThrottlingError:
            self.stdout.write(
                self.style.ERROR(
                    _(f"Transakce je možné stahovat maximálne jednou za 30 sekund.")
                )
            )
        else:
            if not days_argument:
                settings.last_fio_fetch_time = CURRENT_DATETIME()
                settings.save()

            self.stdout.write(self.style.SUCCESS(_(f"Úspěšně stáhnuté transakce.")))
