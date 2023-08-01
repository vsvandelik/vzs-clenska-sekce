import random
from vzs.commands_utils import positive_int, non_negative_int
from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Event
from datetime import datetime, timedelta


def generate_random_datetime():
    while True:
        year = random.randint(2020, 2023)
        month = random.randint(1, 12)
        day = random.randint(1, 31)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        try:
            d = datetime(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                tzinfo=timezone.get_default_timezone(),
            )
            return d
        except ValueError:
            pass


def generate_basic_event(name, min_time_delta_hours, max_time_delta_hours, options):
    if options["time_start"] is not None and options["time_end"] is None:
        time_start = options["time_start"]
        time_end = time_start + timedelta(
            hours=random.randint(min_time_delta_hours, max_time_delta_hours)
        )
    elif options["time_start"] is None and options["time_end"] is not None:
        time_end = options["time_end"]
        time_start = time_end - timedelta(
            hours=random.randint(min_time_delta_hours, max_time_delta_hours)
        )
    elif options["time_start"] is not None and options["time_end"] is not None:
        time_start = options["time_start"]
        time_end = options["time_end"]
        if time_start > time_end:
            time_start, time_end = time_end, time_start
    else:
        time_start = generate_random_datetime()
        time_end = time_start + timedelta(
            hours=random.randint(min_time_delta_hours, max_time_delta_hours)
        )

    capacity = (
        options["capacity"]
        if options["capacity"] is not None
        else random.randint(4, 32)
    )

    min_age = None
    if not options["disable_min_age_restrictions"]:
        if options["min_age"] is not None:
            min_age = options["min_age"]
        elif random.randint(0, 1):
            min_age = random.randint(8, 40)

    event = Event(
        name=name,
        description=f"Tohle je popisek k události {name}",
        time_start=time_start,
        time_end=time_end,
        capacity=capacity,
        min_age=min_age,
        state=Event.State.FUTURE,
    )
    return event


def add_common_args(parser):
    parser.add_argument(
        "N", type=positive_int, help="the number of one time events to create"
    )
    parser.add_argument(
        "-s",
        "--time-start",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M").replace(
            tzinfo=timezone.get_default_timezone()
        ),
        help="the time when the events start in 'Y-m-d H:M' format",
    )
    parser.add_argument(
        "-e",
        "--time-end",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M").replace(
            tzinfo=timezone.get_default_timezone()
        ),
        help="the time when the events end in 'Y-m-d H:M' format",
    )
    parser.add_argument(
        "-c",
        "--capacity",
        type=non_negative_int,
        help="the maximum number of participants",
    )
    parser.add_argument(
        "-a",
        "--min-age",
        type=non_negative_int,
        help="the minimum age of participants",
    )
    parser.add_argument(
        "--disable-age-limit-restrictions",
        action="store_true",
        help="forces the event not to use any age limit restrictions",
    )


class Command(BaseCommand):
    help = "Creates N new one time events to test design with."

    def add_arguments(self, parser):
        add_common_args(parser)

    def handle(self, *args, **options):
        idx = Event.one_time_events.all().count() + 1
        events = []
        for i in range(options["N"]):
            events.append(generate_basic_event(f"událost_{idx}", 2, 168, options))
            idx += 1

        Event.objects.bulk_create(events)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {options["N"]} new one time events.'
            )
        )
