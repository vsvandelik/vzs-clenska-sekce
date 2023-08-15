import random
from django.core.management.base import BaseCommand
from django.utils import timezone

from one_time_events.management.commands.generate_one_time_events import (
    add_common_args,
    generate_basic_event,
)
from events.models import Event, EventOrOccurrenceState
from trainings.utils import weekday_2_day_shortcut
from trainings.models import Training, TrainingOccurrence
from datetime import timedelta, datetime, time


class Command(BaseCommand):
    help = "Creates N new trainings to test design with."

    def _generate_random_time(self):
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        return time(hour=hour, minute=minute)

    def _generate_occurrences(self, event, options):
        date_end = event.date_end
        repeating_a_week = (
            options["conducted_weekly"]
            if options["conducted_weekly"] is not None
            else random.randint(1, 3)
        )
        weekdays = random.sample([0, 1, 2, 3, 4, 5, 6], k=repeating_a_week)
        for weekday in weekdays:
            time_start = self._generate_random_time()
            time_end = self._generate_random_time()
            if time_start > time_end:
                time_start, time_end = time_end, time_start

            day_shortcut = weekday_2_day_shortcut(weekday)
            setattr(event, f"{day_shortcut}_from", time_start)
            setattr(event, f"{day_shortcut}_to", time_end)
            event.save()

            date_start = event.date_start
            while date_start.weekday() != weekday:
                date_start += timedelta(days=1)

            while date_start <= date_end:
                if date_start == date_end or random.randint(1, 10) <= 9:
                    occurrence_start = datetime(
                        year=date_start.year,
                        month=date_start.month,
                        day=date_start.day,
                        hour=time_start.hour,
                        minute=time_start.minute,
                        tzinfo=timezone.get_default_timezone(),
                    )
                    occurrence_end = datetime(
                        year=date_end.year,
                        month=date_end.month,
                        day=date_end.day,
                        hour=time_end.hour,
                        minute=time_end.minute,
                        tzinfo=timezone.get_default_timezone(),
                    )
                    occurrence = TrainingOccurrence(
                        event=event,
                        state=EventOrOccurrenceState.OPEN,
                        datetime_start=occurrence_start,
                        datetime_end=occurrence_end,
                    )
                    occurrence.save()

                date_start += timedelta(days=7)

    def add_arguments(self, parser):
        add_common_args(parser)
        parser.add_argument(
            "-w",
            "--conducted-weekly",
            default=2,
            const=2,
            nargs="?",
            type=int,
            choices=[1, 2, 3],
            help="the number of times the training is conducted weekly",
        )
        parser.add_argument(
            "-k",
            "--category",
            type=Training.Category,
            choices=list(Training.Category),
            help="the category of one time event",
        )

    def handle(self, *args, **options):
        months_six = 182
        idx = Training.objects.all().count() + 1
        for i in range(options["N"]):
            name = f"trénink_{idx}"
            category = (
                options["category"]
                if options["category"] is not None
                else random.choice(Training.Category.choices)[0]
            )

            event = generate_basic_event(
                self, Training.__name__, name, 14, months_six, options
            )
            event.category = category
            event.save()

            self._generate_occurrences(event, options)

            idx += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {options["N"]} new trainings.')
        )
