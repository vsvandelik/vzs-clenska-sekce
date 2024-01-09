from datetime import date, datetime, timedelta
from random import choice as random_choice
from random import randint
from random import sample as random_sample

from django.core.management.base import CommandError

from events.models import EventPersonTypeConstraint
from groups.models import Group
from one_time_events.models import OneTimeEvent
from persons.models import Person
from trainings.models import Training
from vzs.commands_utils import age_int, non_negative_int, positive_int


def _generate_age(min, max):
    if randint(0, 1):
        return randint(min, max)

    return None


def _generate_random_date():
    while True:
        year = randint(2020, 2023)
        month = randint(1, 12)
        day = randint(1, 31)

        try:
            return date(year=year, month=month, day=day)
        except ValueError:
            pass


def generate_min_max_age(options):
    in_age_min = options["min_age"]
    in_age_max = options["max_age"]
    disable_age_restrictions = options["disable_age_restrictions"]

    if in_age_min is not None and in_age_max is not None and in_age_min > in_age_max:
        raise CommandError("Supplied --min-age has greater value than --max-age")

    if disable_age_restrictions:
        return None, None

    valid_range_min = 1
    valid_range_max = 99

    out_age_min = in_age_min or _generate_age(
        valid_range_min, in_age_max or valid_range_max
    )
    out_age_max = in_age_max or _generate_age(
        out_age_min or valid_range_min, valid_range_max
    )

    return out_age_min, out_age_max


def generate_group_requirement(options):
    groups_count = Group.objects.all().count()
    group = None
    if not options["disable_group_restrictions"]:
        if groups_count == 0 and options["requires_group"]:
            raise CommandError("--requires-group requires an existing group in the DB")
        elif groups_count > 0 and (options["requires_group"] or bool(randint(0, 1))):
            group = Group.objects.order_by("?").first()
    return group


def generate_allowed_person_types_requirement(options):
    chosen_person_types = []
    if options["person_type"] is None:
        if randint(1, 10) > 6:
            person_types = list(Person.Type.values)
            chosen_person_types = random_sample(
                person_types, k=randint(0, len(person_types) - 1)
            )
    else:
        chosen_person_types = [
            person_type.value for person_type in options["person_type"]
        ]

    return [
        EventPersonTypeConstraint.get_or_create(person_type)
        for person_type in chosen_person_types
    ]


def _generate_start_end_dates(min_days_delta, max_days_delta, options):
    if options["date_start"] is not None and options["date_end"] is None:
        date_start = options["date_start"]
        date_end = date_start + timedelta(days=randint(min_days_delta, max_days_delta))
    elif options["date_start"] is None and options["date_end"] is not None:
        date_end = options["date_end"]
        date_start = date_end - timedelta(days=randint(min_days_delta, max_days_delta))
    elif options["date_start"] is not None and options["date_end"] is not None:
        date_start = options["date_start"]
        date_end = options["date_end"]
        if date_start > date_end:
            raise CommandError("--date-start has greater value than --date-end")
    else:
        date_start = _generate_random_date()
        date_end = date_start + timedelta(days=randint(min_days_delta, max_days_delta))
    return date_start, date_end


def generate_basic_event(t, name, min_days_delta, max_days_delta, options):
    date_start, date_end = _generate_start_end_dates(
        min_days_delta, max_days_delta, options
    )

    capacity = (
        options["capacity"] if options["capacity"] is not None else randint(4, 32)
    )

    location = random_choice(
        [
            "klubovna",
            "tělocvična",
            "sportoviště",
            "hriště",
            "orlická přehrada",
            "plavecký bazén",
            "učebna",
        ]
    )

    min_age, max_age = generate_min_max_age(options)
    group = generate_group_requirement(options)
    allowed_person_types = generate_allowed_person_types_requirement(options)

    if t == OneTimeEvent.__name__:
        event = OneTimeEvent(
            name=name,
            description=f"Tohle je popisek k události {name}",
            date_start=date_start,
            date_end=date_end,
            capacity=capacity,
            location=location,
            min_age=min_age,
            max_age=max_age,
            group=group,
        )
    elif t == Training.__name__:
        event = Training(
            name=name,
            description=f"Tohle je popisek k události {name}",
            date_start=date_start,
            date_end=date_end,
            capacity=capacity,
            location=location,
            min_age=min_age,
            max_age=max_age,
            group=group,
        )
    else:
        raise NotImplementedError

    event.save()
    for person_type in allowed_person_types:
        event.allowed_person_types.add(person_type)

    return event


def add_common_args(parser):
    parser.add_argument(
        "N", type=positive_int, help="the number of one time events to create"
    )
    parser.add_argument(
        "-s",
        "--date-start",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        help="the date when the events start in 'Y-m-d' format",
    )
    parser.add_argument(
        "-e",
        "--date-end",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        help="the date when the events end in 'Y-m-d' format",
    )
    parser.add_argument(
        "-c",
        "--capacity",
        type=non_negative_int,
        help="the maximum number of participants",
    )
    parser.add_argument(
        "--min-age",
        type=age_int,
        help="the minimum age of participants",
    )
    parser.add_argument(
        "--max-age",
        type=age_int,
        help="the maximum age of participants",
    )
    parser.add_argument(
        "--disable-age-restrictions",
        action="store_true",
        help="forces the event not to use any age limit restrictions",
    )
    parser.add_argument(
        "--disable-group-restrictions",
        action="store_true",
        help="forces the event not to use group membership limitation for participants (overrides --requires-group arg)",
    )
    parser.add_argument(
        "-g",
        "--requires-group",
        action="store_true",
        help="forces the event to use group membership limitation for participants (won't be fulfilled if there does not exist any group)",
    )
    parser.add_argument(
        "-p",
        "--person-type",
        type=Person.Type,
        nargs="*",
        choices=list(Person.Type),
        help="forces the event to allow only a specific person types for participants",
    )
