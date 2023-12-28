from random import randint

from django.core.management.base import BaseCommand, CommandError

from events.management.commands.generate_basic_event import (
    generate_allowed_person_types_requirement,
    generate_group_requirement,
    generate_min_max_age,
)
from features.models import Feature
from persons.models import Person
from positions.models import EventPosition
from vzs.commands_utils import age_int, non_negative_int, positive_int


class Command(BaseCommand):
    help = "Creates N new positions to test design with."

    def _generate_required_features(self, options):
        all_features_count = Feature.objects.all().count()

        features_to_add_count = options["features_count"]

        if features_to_add_count is not None:
            if all_features_count < features_to_add_count:
                raise CommandError(
                    f"The DB does not contain {features_to_add_count} features"
                )
        else:
            features_to_add_count = randint(0, all_features_count)

        return Feature.objects.order_by("?")[:features_to_add_count]

    def add_arguments(self, parser):
        parser.add_argument(
            "N", type=positive_int, help="the number of positions to create"
        )
        parser.add_argument(
            "-f",
            "--features-count",
            type=non_negative_int,
            help="the number of required features for the position",
        )
        parser.add_argument(
            "--min-age",
            type=age_int,
            help="the minimal allowed age for the position",
        )
        parser.add_argument(
            "--max-age",
            type=age_int,
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
            help="forces the position not to use group membership limitation (overrides --requires-group arg)",
        )
        parser.add_argument(
            "-g",
            "--requires-group",
            action="store_true",
            help="forces the position to use group membership limitation (won't be fulfilled if there does not exist any group)",
        )
        parser.add_argument(
            "-t",
            "--person-type",
            type=Person.Type,
            nargs="*",
            choices=list(Person.Type),
            help="forces the positions to allow only a specific person types",
        )
        parser.add_argument(
            "-w",
            "--wage",
            type=positive_int,
            help="the hourly wage for organizers",
        )

    def handle(self, *args, **options):
        to_create_count = options["N"]

        index_start = EventPosition.objects.all().count() + 1
        index_end = index_start + to_create_count

        for i in range(index_start, index_end):
            name = f"pozice_{i}"
            required_features = self._generate_required_features(options)
            min_age, max_age = generate_min_max_age(options)
            group = generate_group_requirement(options)
            allowed_person_types = generate_allowed_person_types_requirement(options)

            wage_hour = (
                options["wage"] if options["wage"] is not None else randint(1, 1000)
            )

            position = EventPosition(
                name=name,
                min_age=min_age,
                max_age=max_age,
                group=group,
                wage_hour=wage_hour,
            )
            position.save()

            for feature in required_features:
                position.required_features.add(feature)

            for person_type in allowed_person_types:
                position.allowed_person_types.add(person_type)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {to_create_count} new positions.")
        )
