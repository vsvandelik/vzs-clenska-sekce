from persons.utils import fetch_fio
from persons.models import FioSettings

from fiobank import ThrottlingError

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from datetime import timedelta


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
        now = timezone.now()

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
                settings.last_fio_fetch_time = timezone.now()
                settings.save()

            self.stdout.write(self.style.SUCCESS(_(f"Úspěšně stáhnuté transakce.")))