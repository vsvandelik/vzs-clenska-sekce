import random

from argparse import ArgumentTypeError
from django.core.management.base import BaseCommand

from positions.models import EventPosition, PersonType
from events.models import Event
from datetime import datetime


def lower_bounded_int(value, lower_bound):
    v = int(value)
    if v < lower_bound:
        raise ArgumentTypeError(f"{v} is an invalid value")
    return v


def positive_int(value):
    return lower_bounded_int(value, 1)


def non_negative_int(value):
    return lower_bounded_int(value, 0)


def generate_basic_event(name, options):
    event = Event(
        name=name,
        description=f"Tohle je popisek k události {name}",
    )


class Command(BaseCommand):
    help = "Creates N new one time events to test design with."

    def add_arguments(self, parser):
        parser.add_argument(
            "N", type=positive_int, help="the number of one time events to create"
        )
        parser.add_argument(
            "-s",
            "--time-start",
            type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
            help="the time when the events start",
        )
        parser.add_argument(
            "-e",
            "--time-end",
            type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
            help="the time when the events end",
        )
        parser.add_argument(
            "-c",
            "--capacity",
            type=non_negative_int,
            help="the maximum number of participants",
        )
        parser.add_argument(
            "-a",
            "--age-limit",
            type=non_negative_int,
            help="the minimum age of participants",
        )

    def handle(self, *args, **options):
        idx = Event.one_time_events.all().count() + 1
        for i in range(options["N"]):
            pass

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {options["N"]} new one time events.'
            )
        )
