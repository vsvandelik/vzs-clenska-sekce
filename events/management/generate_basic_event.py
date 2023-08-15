import random
from vzs.commands_utils import positive_int, non_negative_int
from django.utils import timezone
from one_time_events.models import OneTimeEvent
from trainings.models import Training
from persons.models import Person, PersonType
from datetime import datetime, timedelta, date
from groups.models import Group


def _generate_age(min, max):
    if random.randint(0, 1):
        return random.randint(min, max)
    return None


def _generate_random_date():
    while True:
        year = random.randint(2020, 2023)
        month = random.randint(1, 12)
        day = random.randint(1, 31)
        try:
            return date(year=year, month=month, day=day)
        except ValueError:
            pass


def generate_min_max_age(cmd_obj, options):
    values = {}
    if options["disable_age_restrictions"]:
        values["min_age"] = None
        values["max_age"] = None
    else:
        if options["min_age"] is not None:
            values["min_age"] = options["min_age"]

        if options["max_age"] is not None:
            values["max_age"] = options["max_age"]

        if "min_age" not in values and "max_age" in values:
            values["min_age"] = _generate_age(1, values["max_age"])

        elif "max_age" not in values and "min_age" in values:
            values["max_age"] = _generate_age(values["min_age"], 99)

        elif (
            options["min_age"] is not None
            and options["max_age"] is not None
            and options["min_age"] > options["max_age"]
        ):
            cmd_obj.stdout.write(
                cmd_obj.style.WARNING(
                    f"Supplied --min-age has greater value than --max-age, switching the values"
                )
            )
            values["min_age"], values["max_age"] = values["max_age"], values["min_age"]

        elif "min_age" not in values and "max_age" not in values:
            values["min_age"] = _generate_age(1, 40)
            values["max_age"] = _generate_age(1, 99)

    return values["min_age"], values["max_age"]


def generate_group_requirement(cmd_obj, options):
    groups_count = Group.objects.all().count()
    group = None
    if not options["disable_group_restrictions"]:
        if groups_count == 0 and options["requires_group"]:
            cmd_obj.stdout.write(
                cmd_obj.style.WARNING(
                    f"Ignoring --requires-group flag due to nonexistent group in the system"
                )
            )
        elif groups_count > 0 and (
            options["requires_group"] or bool(random.randint(0, 1))
        ):
            group = Group.objects.order_by("?").first()
    return group


def _retrieve_person_type(person_type):
    queryset = PersonType.objects.filter(person_type=person_type)
    if queryset.count() == 0:
        person_type = PersonType(person_type=person_type)
        person_type.save()
        return person_type
    return queryset[0]


def generate_allowed_person_types_requirement(options):
    chosen_person_types = []
    if options["person_type"] is None:
        if random.randint(1, 10) > 6:
            person_types = list(Person.Type.values)
            chosen_person_types = random.sample(
                person_types, k=random.randint(0, len(person_types) - 1)
            )
    else:
        chosen_person_types = map(lambda x: x.value, options["person_type"])

    return map(_retrieve_person_type, chosen_person_types)


def _generate_start_end_dates(cmd_obj, min_days_delta, max_days_delta, options):
    if options["date_start"] is not None and options["date_end"] is None:
        date_start = options["date_start"]
        date_end = date_start + timedelta(
            days=random.randint(min_days_delta, max_days_delta)
        )
    elif options["date_start"] is None and options["date_end"] is not None:
        date_end = options["date_end"]
        date_start = date_end - timedelta(
            days=random.randint(min_days_delta, max_days_delta)
        )
    elif options["date_start"] is not None and options["date_end"] is not None:
        date_start = options["date_start"]
        date_end = options["date_end"]
        if date_start > date_end:
            cmd_obj.stdout.write(
                cmd_obj.style.WARNING(
                    f"Supplied --date-start has greater value than --date-end, switching the values"
                )
            )
            date_start, date_end = date_end, date_start
    else:
        date_start = _generate_random_date()
        date_end = date_start + timedelta(
            days=random.randint(min_days_delta, max_days_delta)
        )
    return date_start, date_end


def generate_basic_event(cmd_obj, type, name, min_days_delta, max_days_delta, options):
    date_start, date_end = _generate_start_end_dates(
        cmd_obj, min_days_delta, max_days_delta, options
    )

    capacity = (
        options["capacity"]
        if options["capacity"] is not None
        else random.randint(4, 32)
    )

    location = random.choice(
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

    min_age, max_age = generate_min_max_age(cmd_obj, options)
    group = generate_group_requirement(cmd_obj, options)
    allowed_person_types = generate_allowed_person_types_requirement(options)

    if type == OneTimeEvent.__name__:
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
    elif type == Training.__name__:
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
        type=lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M")
        .replace(tzinfo=timezone.get_default_timezone())
        .date(),
        help="the time when the events start in 'Y-m-d H:M' format",
    )
    parser.add_argument(
        "-e",
        "--date-end",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M")
        .replace(tzinfo=timezone.get_default_timezone())
        .date(),
        help="the time when the events end in 'Y-m-d H:M' format",
    )
    parser.add_argument(
        "-c",
        "--capacity",
        type=non_negative_int,
        help="the maximum number of participants",
    )
    parser.add_argument(
        "--min-age",
        type=non_negative_int,
        help="the minimum age of participants",
    )
    parser.add_argument(
        "--max-age",
        type=non_negative_int,
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
        "-t",
        "--person-type",
        type=Person.Type,
        nargs="*",
        choices=list(Person.Type),
        help="forces the event to allow only a specific person types for participants",
    )
