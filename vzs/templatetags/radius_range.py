from django import template

register = template.Library()


@register.filter
def radius_range(center, radius):
    return range(center - radius, center + radius + 1)
