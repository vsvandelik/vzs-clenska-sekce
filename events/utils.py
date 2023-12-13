from datetime import datetime
from persons.models import Person


def parse_czech_date(date_str):
    return datetime.strptime(date_str, "%d. %m. %Y")


def check_common_requirements(req_obj, person):
    from events.models import EventPersonTypeConstraint

    person_with_age = Person.objects.with_age().get(id=person.id)

    missing_age = person_with_age.age is None and (
        req_obj.min_age is not None or req_obj.max_age is not None
    )

    min_age_out = req_obj.min_age is not None and (
        missing_age or req_obj.min_age > person_with_age.age
    )
    max_age_out = req_obj.max_age is not None and (
        missing_age or req_obj.max_age < person_with_age.age
    )
    group_unsatisfied = (
        req_obj.group is not None and req_obj.group not in person.groups.all()
    )
    allowed_person_types_unsatisfied = (
        req_obj.allowed_person_types.exists()
        and not req_obj.allowed_person_types.contains(
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
