from typing import Annotated, TypedDict

from django.db.models import Q

from persons.models import Person
from vzs.datetime_constants import (
    DAY_IN_WEEK_NAMES,
    DAY_IN_WEEK_SHORTCUTS,
    DAY_IN_WEEK_SHORTCUTS_PRETTY,
)
from vzs.utils import today


def weekday_2_day_shortcut(weekday):
    return days_shortcut_list()[weekday]


def day_shortcut_pretty(day_shortcut):
    return days_pretty_list()[day_shortcut_2_weekday(day_shortcut)]


def day_shortcut_2_weekday(day_shortcut):
    return days_shortcut_list().index(day_shortcut)


def weekday_pretty(weekday):
    return days_pretty_list()[weekday]


def weekday_pretty_full_name(weekday):
    return DAY_IN_WEEK_NAMES[weekday]


def days_shortcut_list():
    return DAY_IN_WEEK_SHORTCUTS


def days_pretty_list():
    return DAY_IN_WEEK_SHORTCUTS_PRETTY


class TrainingsFilter(TypedDict, total=False):
    """
    Defines a filter for trainings.

    Use with :func:`vzs.utils.filter_queryset`.
    """

    category: Annotated[str, lambda category: Q(category=category)]

    year_start: Annotated[int, lambda year_start: Q(date_start__year=year_start)]

    main_coach: Annotated[
        Person, lambda main_coach: Q(main_coach_assignment__person=main_coach)
    ]

    only_opened: Annotated[
        str,
        lambda only_opened: Q(date_end__gte=today()) if only_opened == "yes" else Q(),
    ]
