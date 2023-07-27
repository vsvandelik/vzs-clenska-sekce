import random
from django.core.management.base import BaseCommand
from django.utils import timezone

from .generate_one_time_events import add_common_args, generate_basic_event
from events.models import Event
from datetime import timedelta, datetime


class Command(BaseCommand):
    help = "Creates N new trainings to test design with."

    def add_arguments(self, parser):
        add_common_args(parser)
        parser.add_argument(
            "-k",
            "--conducted-weekly",
            default=2,
            const=2,
            nargs="?",
            type=int,
            choices=[1, 2, 3],
            help="the number of times the training is conducted weekly",
        )

    def handle(self, *args, **options):
        days_14 = 336
        months_six = 4368
        idx = Event.parent_trainings.all().count() + 1
        for i in range(options["N"]):
            repeating_a_week = (
                options["conducted_weekly"]
                if options["conducted_weekly"] is not None
                else random.randint(1, 3)
            )
            weekdays = random.sample([0, 1, 2, 3, 4, 5, 6], k=repeating_a_week)

            parent_event = generate_basic_event(
                f"trénink_{idx}", days_14, months_six, options
            )
            parent_event.save()
            parent_id = parent_event.id

            time_start = parent_event.time_start
            time_end = parent_event.time_end

            end_date = time_end.date()

            for weekday in weekdays:
                start_date = time_start.date()
                while start_date.weekday() != weekday:
                    start_date += timedelta(days=1)

                while start_date <= end_date:
                    if start_date == time_start.date() or random.randint(1, 10) <= 9:
                        child_start = datetime(
                            year=start_date.year,
                            month=start_date.month,
                            day=start_date.day,
                            hour=time_start.hour,
                            minute=time_start.minute,
                            tzinfo=timezone.get_default_timezone(),
                        )
                        child_end = datetime(
                            year=start_date.year,
                            month=start_date.month,
                            day=start_date.day,
                            hour=time_end.hour,
                            minute=time_end.minute,
                            tzinfo=timezone.get_default_timezone(),
                        )

                        child = parent_event
                        child.pk = None
                        child.parent_id = parent_id
                        child.time_start = child_start
                        child.time_end = child_end
                        child.save()
                    start_date += timedelta(days=7)
            idx += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {options["N"]} new trainings.')
        )
