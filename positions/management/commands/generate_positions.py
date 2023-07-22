import random

from argparse import ArgumentTypeError
from django.core.management.base import BaseCommand

from positions.models import EventPosition, PersonType
from persons.models import Person
from features.models import Feature
from groups.models import Group


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

    def handle(self, *args, **options):
        idx = EventPosition.objects.all().count() + 1
        features_length = Feature.objects.all().count()
        min_age = None
        max_age = None
        if options["disable_age_restrictions"]:
            min_age_enabled = False
            max_age_enabled = False
        if options["disable_group_restrictions"]:
            group_membership_required = False
            group = None
        for i in range(options["N"]):
            name = f"pozice_{idx}"
            if not options["disable_age_restrictions"]:
                if options["min_age"] is not None:
                    min_age_enabled = True
                    min_age = options["min_age"]
                else:
                    min_age_enabled = bool(random.randint(0, 1))
                    if min_age_enabled:
                        min_age = random.randint(1, 99)
                        if max_age is not None:
                            while max_age < min_age:
                                min_age = random.randint(1, 99)
                    else:
                        min_age = None
                if options["max_age"] is not None:
                    max_age_enabled = True
                    max_age = options["max_age"]
                else:
                    max_age_enabled = bool(random.randint(0, 1))
                    if max_age_enabled:
                        max_age = random.randint(1, 99)
                        if min_age is not None:
                            while max_age < min_age:
                                max_age = random.randint(1, 99)
                    else:
                        max_age = None
                if (
                    options["min_age"] is not None
                    and options["max_age"] is not None
                    and min_age > max_age
                ):
                    self.stdout.write(
                        self.style.WARNING(
                            "--min-age is greater than --max-age, swapping the values"
                        )
                    )
                    min_age, max_age = max_age, min_age

            if options["features_count"] is not None:
                features_to_add = min(options["features_count"], features_length)
                if features_to_add < options["features_count"]:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Limiting required features to {features_to_add} due to insufficient number of features"
                        )
                    )
            else:
                features_to_add = random.randint(0, features_length)

            required_features = Feature.objects.order_by("?")[:features_to_add]

            if not options["disable_group_restrictions"]:
                if options["required_group"]:
                    group_membership_required = True
                    group = Group.objects.order_by("?").first()
                else:
                    group_membership_required = bool(random.randint(0, 1))
                    if group_membership_required:
                        group = Group.objects.order_by("?").first()
                    else:
                        group = None

            if options["person_type"] is None:
                person_types = list(Person.Type.values)
                chosen_person_types = random.sample(
                    person_types, k=random.randint(0, len(person_types) - 1)
                )
            else:
                chosen_person_types = map(lambda x: x.value, options["person_type"])
            allowed_person_types = map(self.retrieve_person_type, chosen_person_types)

            position = EventPosition(
                name=name,
                min_age_enabled=min_age_enabled,
                max_age_enabled=max_age_enabled,
                min_age=min_age,
                max_age=max_age,
                group_membership_required=group_membership_required,
                group=group,
            )

            position.save()

            for feature in required_features:
                position.required_features.add(feature)

            for person_type in allowed_person_types:
                position.allowed_person_types.add(person_type)

            idx += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {options["N"]} new positions.')
        )
