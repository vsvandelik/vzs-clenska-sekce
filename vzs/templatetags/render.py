from django import template

register = template.Library()


@register.simple_tag
def render(instance, style, **kwargs):
    return instance.render(style, **kwargs)
