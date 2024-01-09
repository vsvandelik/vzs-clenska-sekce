from datetime import date, datetime

from persons.models import Person


def parse_czech_date(date_str) -> date:
    """
    Parses a date string in the format ``DD. MM. YYYY``.
    """

    return datetime.strptime(date_str, "%d. %m. %Y").date()


def check_common_requirements(event_or_position, person: Person) -> bool:
    """
    Checks for common requirements of events or event positions.

    Namely:
    *   minimum age
    *   maximum age
    *   group
    *   allowed person types
    """

    from events.models import EventPersonTypeConstraint

    person_with_age = Person.objects.with_age().get(id=person.id)

    missing_age = person_with_age.age is None and (
        event_or_position.min_age is not None or event_or_position.max_age is not None
    )

    min_age_out = event_or_position.min_age is not None and (
        missing_age or event_or_position.min_age > person_with_age.age
    )

    max_age_out = event_or_position.max_age is not None and (
        missing_age or event_or_position.max_age < person_with_age.age
    )

    group_unsatisfied = (
        event_or_position.group is not None
        and event_or_position.group not in person.groups.all()
    )

    allowed_person_types_unsatisfied = (
        event_or_position.allowed_person_types.exists()
        and not event_or_position.allowed_person_types.contains(
            EventPersonTypeConstraint.get_or_create(person.person_type)
        )
    )

    if (
        missing_age
        or min_age_out
        or max_age_out
        or group_unsatisfied
        or allowed_person_types_unsatisfied
    ):
        return False

    return True
