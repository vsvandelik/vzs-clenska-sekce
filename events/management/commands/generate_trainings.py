import random

from argparse import ArgumentTypeError
from django.core.management.base import BaseCommand

from positions.models import EventPosition, PersonType
from events.models import Event
from . import generate_one_time_events


def lower_bounded_int(value, lower_bound):
    v = int(value)
    if v < lower_bound:
        raise ArgumentTypeError(f"{v} is an invalid value")
    return v


def positive_int(value):
    return lower_bounded_int(value, 1)


def non_negative_int(value):
    return lower_bounded_int(value, 0)


class Command(BaseCommand):
    help = "Creates N new trainings to test design with."

    def add_arguments(self, parser):
        parser.add_argument(
            "N", type=positive_int, help="the number of trainings to create"
        )

    def handle(self, *args, **options):
        idx = Event.one_time_events.all().count() + 1
        for i in range(options["N"]):
            pass

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {options["N"]} new trainings.')
        )
