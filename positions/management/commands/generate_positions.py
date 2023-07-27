import random

from argparse import ArgumentTypeError
from django.core.management.base import BaseCommand

from positions.models import EventPosition, PersonType
from persons.models import Person
from features.models import Feature
from groups.models import Group
from events.management.commands.generate_one_time_events import (
    positive_int,
    non_negative_int,
)


class Command(BaseCommand):
    help = "Creates N new positions to test design with."

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
            type=positive_int,
            help="the minimal allowed age for the position",
        )
        parser.add_argument(
            "--max-age",
            type=positive_int,
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
            help="forces the positions to allow only a specific person type",
        )

    def retrieve_person_type(self, person_type):
        queryset = PersonType.objects.filter(person_type=person_type)
        if queryset.count() == 0:
            person_type = PersonType(person_type=person_type)
            person_type.save()
            return person_type
        return queryset[0]

    def generate_age(self, min, max):
        if random.randint(0, 1):
            return random.randint(min, max), True
        return None, False

    def handle(self, *args, **options):
        idx = EventPosition.objects.all().count() + 1
        all_features_count = Feature.objects.all().count()
        groups_count = Group.objects.all().count()
        values = {}

        if options["disable_group_restrictions"]:
            group_membership_required = False
            group = None

        if groups_count == 0 and options["requires_group"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Ignoring --requires-group flag due to nonexistent group in the system"
                )
            )

        for i in range(options["N"]):
            position_name = f"pozice_{idx}"

            if options["disable_age_restrictions"]:
                values["min_age_enabled"] = False
                values["max_age_enabled"] = False
                values["min_age"] = None
                values["max_age"] = None
            else:
                if options["min_age"] is not None:
                    values["min_age"] = options["min_age"]
                if options["max_age"] is not None:
                    values["max_age"] = options["max_age"]
                if "min_age" not in values and "max_age" in values:
                    values["min_age"], values["min_age_enabled"] = self.generate_age(
                        1, values["max_age"]
                    )
                    values["max_age_enabled"] = True
                elif "max_age" not in values and "min_age" in values:
                    values["max_age"], values["max_age_enabled"] = self.generate_age(
                        values["min_age"], 99
                    )
                    values["min_age_enabled"] = True
                elif "min_age" not in values and "max_age" not in values:
                    values["min_age"], values["min_age_enabled"] = self.generate_age(
                        1, 99
                    )
                    values["max_age"], values["max_age_enabled"] = self.generate_age(
                        1, 99
                    )
                    if (
                        values["min_age_enabled"]
                        and values["max_age_enabled"]
                        and values["min_age"] > values["max_age"]
                    ):
                        values["min_age"], values["max_age"] = (
                            values["max_age"],
                            values["min_age"],
                        )

            if options["features_count"] is not None:
                features_to_add_count = min(
                    options["features_count"], all_features_count
                )
                if features_to_add_count < options["features_count"]:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Limiting required features to {features_to_add_count} due to insufficient number of features"
                        )
                    )
            else:
                features_to_add_count = random.randint(0, all_features_count)

            required_features = Feature.objects.order_by("?")[:features_to_add_count]

            if not options["disable_group_restrictions"]:
                if groups_count > 0 and (
                    options["requires_group"] or bool(random.randint(0, 1))
                ):
                    group_membership_required = True
                    group = Group.objects.order_by("?").first()
                else:
                    group_membership_required = False
                    group = None

            position = EventPosition(
                name=position_name,
                min_age_enabled=values["min_age_enabled"],
                max_age_enabled=values["max_age_enabled"],
                min_age=values["min_age"],
                max_age=values["max_age"],
                group_membership_required=group_membership_required,
                group=group,
            )
            position.save()

            if options["person_type"] is None:
                person_types = list(Person.Type.values)
                chosen_person_types = random.sample(
                    person_types, k=random.randint(0, len(person_types) - 1)
                )
            else:
                chosen_person_types = map(lambda x: x.value, options["person_type"])
            allowed_person_types = map(self.retrieve_person_type, chosen_person_types)

            for feature in required_features:
                position.required_features.add(feature)

            for person_type in allowed_person_types:
                position.allowed_person_types.add(person_type)

            values.clear()
            idx += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {options["N"]} new positions.')
        )
