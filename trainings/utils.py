from vzs.datetime_constants import (
    DAY_IN_WEEK_NAMES,
    DAY_IN_WEEK_SHORTCUTS,
    DAY_IN_WEEK_SHORTCUTS_PRETTY,
)


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
