import random

from django.core.management.base import BaseCommand

from positions.models import EventPosition
from persons.models import Person


class Command(BaseCommand):
    help = "Creates N new positions to test design with."

    def add_arguments(self, parser):
        parser.add_argument("N", type=int, help="the number of positions to create")
        parser.add_argument(
            "-f",
            "--features-count",
            type=int,
            help="the number of required features for the position",
        )
        parser.add_argument(
            "--min-age",
            type=int,
            help="the minimal allowed age for the position",
        )
        parser.add_argument(
            "--max-age",
            type=int,
            help="the maximal allowed age for the position",
        )
        parser.add_argument(
            "--disable-age-restrictions",
            action="store_true",
            help="forces the position not to use any age limits (overrides --min-age, --max-age args)",
        )
        parser.add_argument(
            "--disable-group-restrictions",
            action="store_true",
            help="forces the position not to use group membership limitation (overrides --required-group arg)",
        )
        parser.add_argument(
            "-g",
            "--required-group",
            action="store_true",
            help="forces the position to use group membership limitation (won't be fulfilled if there does not exist any group)",
        )
        parser.add_argument(
            "-t",
            "--person-type",
            type=Person.Type,
            choices=list(Person.Type),
            help="forces the positions to allow only a specific person type",
        )

    def handle(self, *args, **options):
        idx = EventPosition.objects.all().count() + 1
        name = f"pozice_{idx}"
        if options["disable-age-restrictions"]:
            min_age_enabled = False
            max_age_enabled = False
        else:
            if options["min_age"] is not None:
                pass

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {options["N"]} new price_lists.')
        )
