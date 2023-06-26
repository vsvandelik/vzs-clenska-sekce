from django import template

register = template.Library()


@register.filter
def bool_cz(value):
    if value:
        return "Ano"
    else:
        return "Ne"


@register.simple_tag
def render(instance, style, **kwargs):
    return instance.render(style, **kwargs)


@register.filter
def radius_range(center, radius):
    return range(center - radius, center + radius + 1)


@register.filter
def neq(left, right):
    return left != right
