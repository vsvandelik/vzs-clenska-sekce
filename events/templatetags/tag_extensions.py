import re
from django import template
from ..utils import day_shortcut_2_weekday as day_shortcut_2_weekday_impl
from ..utils import weekday_pretty as weekday_pretty_impl
from ..utils import weekday_2_day_shortcut as weekday_2_day_shortcut_impl
from ..models import EventParticipation

numeric_test = re.compile("^\d+$")
register = template.Library()


@register.filter
def getattribute(value, arg):
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, "has_key") and value.has_key(arg):
        return value[arg]
    elif numeric_test.match(str(arg)) and len(value) > int(arg):
        return value[int(arg)]
    else:
        return None


@register.filter
def day_shortcut_2_weekday(value):
    return day_shortcut_2_weekday_impl(value)


@register.filter
def weekday_2_day_shortcut(value):
    return weekday_2_day_shortcut_impl(value)


@register.filter
def weekday_pretty(value):
    return weekday_pretty_impl(value)


@register.filter
def date_get_weekday(date):
    return date.weekday()


@register.filter
def addstr(arg1, arg2):
    return str(arg1) + str(arg2)


@register.filter
def index(indexable, i):
    return indexable[i]


@register.filter
def index_safe(indexable, i):
    if indexable in [None, ""]:
        return iter([])
    if i in indexable:
        return indexable[i]
    return iter([])


@register.filter
def field_value(fields, field_name):
    return fields[field_name].value()


@register.filter
def atoi(value):
    return int(value)


@register.filter
def is_approved_participant(person, event):
    return (
        EventParticipation.objects.filter(
            event=event, person=person, state=EventParticipation.State.APPROVED
        ).count()
        == 1
    )


@register.filter
def is_substitution_participant(person, event):
    return (
        EventParticipation.objects.filter(
            event=event, person=person, state=EventParticipation.State.SUBSTITUTE
        ).count()
        == 1
    )


@register.filter
def is_waiting_participant(person, event):
    return (
        EventParticipation.objects.filter(
            event=event, person=person, state=EventParticipation.State.WAITING
        ).count()
        == 1
    )
