from django import template

register = template.Library()


@register.filter
def bool_cz(value):
    if value:
        return "Ano"
    else:
        return "Ne"
