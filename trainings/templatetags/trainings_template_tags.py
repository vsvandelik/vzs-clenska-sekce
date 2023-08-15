from django import template
from ..utils import day_shortcut_2_weekday as day_shortcut_2_weekday_impl
from ..utils import weekday_pretty as weekday_pretty_impl
from ..utils import weekday_2_day_shortcut as weekday_2_day_shortcut_impl
from ..utils import day_shortcut_pretty as day_shortcut_pretty_impl

register = template.Library()


@register.filter
def day_shortcut_2_weekday(value):
    return day_shortcut_2_weekday_impl(value)


@register.filter
def weekday_2_day_shortcut(value):
    return weekday_2_day_shortcut_impl(value)


@register.filter
def day_shortcut_pretty(value):
    return day_shortcut_pretty_impl(value)


@register.filter
def weekday_pretty(value):
    return weekday_pretty_impl(value)


@register.filter
def date_get_weekday(date):
    return date.weekday()