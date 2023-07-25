import random

from argparse import ArgumentTypeError
from django.core.management.base import BaseCommand

from .generate_one_time_events import add_common_args, generate_basic_event
from events.models import Event


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
        add_common_args(parser)
        parser.add_argument(
            "-k",
            "--conducted-weekly",
            default=2,
            const=2,
            nargs="?",
            choices=[1, 2, 3],
            help="the number of times the training is conducted weekly",
        )

    def handle(self, *args, **options):
        idx = Event.parent_trainings.all().count() + 1
        events = []
        for i in range(options["N"]):
            repeating_a_week = random.randint(1, 3)
            weekdays = random.sample([0, 1, 2, 3, 4, 5, 6], k=repeating_a_week)

            parent_event = generate_basic_event(f"událost_{idx}", 336, 4368, options)
            parent_event.save()

            # TODO

            events.append()
            idx += 1

        Event.objects.bulk_create(events)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {options["N"]} new trainings.')
        )
