import random
from django.core.management.base import BaseCommand
from events.management.generate_basic_event import generate_basic_event, add_common_args
from events.models import EventOrOccurrenceState
from one_time_events.models import OneTimeEvent, OneTimeEventOccurrence
from vzs.commands_utils import non_negative_int
from datetime import timedelta


class Command(BaseCommand):
    help = "Creates N new one time events to test design with."

    def add_arguments(self, parser):
        add_common_args(parser)

        parser.add_argument(
            "-f",
            "--default-participation-fee",
            type=non_negative_int,
            help="the default value for participation fee",
        )
        parser.add_argument(
            "-k",
            "--category",
            type=OneTimeEvent.Category,
            choices=list(OneTimeEvent.Category),
            help="the category of one time event",
        )

    def _generate_occurrences(self, event):
        date_start = event.date_start
        date_end = event.date_end
        while date_start <= date_end:
            if random.randint(1, 10) <= 8 or event.date_start == date_start:
                hours = (
                    10 if event.date_start != event.date_end else random.randint(1, 10)
                )
                occurrence = OneTimeEventOccurrence(
                    date=date_start,
                    hours=hours,
                    state=EventOrOccurrenceState.OPEN,
                    event=event,
                )
                occurrence.save()
            date_start += timedelta(days=1)

    def handle(self, *args, **options):
        idx = OneTimeEvent.objects.all().count() + 1
        for i in range(options["N"]):
            name = f"jednorázová_{idx}"

            default_participation_fee = (
                options["default_participation_fee"]
                if options["default_participation_fee"] is not None
                else random.randint(0, 5000)
                if random.randint(0, 1)
                else None
            )

            category = (
                options["category"]
                if options["category"] is not None
                else random.choice(OneTimeEvent.Category.choices)[0]
            )

            event = generate_basic_event(OneTimeEvent.__name__, name, 0, 7, options)
            event.default_participation_fee = default_participation_fee
            event.state = EventOrOccurrenceState.OPEN
            event.category = category
            event.save()

            self._generate_occurrences(event)

            idx += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {options["N"]} new one time events.'
            )
        )
