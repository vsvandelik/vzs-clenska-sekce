from django import template
from django.utils.safestring import mark_safe

from vzs import settings

register = template.Library()


@register.filter
def bool_js(value, opposite=False):
    if opposite:
        value = not value

    if value:
        return "true"
    else:
        return "false"


@register.simple_tag
def render(instance, style, **kwargs):
    return instance.render(style, **kwargs)


@register.filter
def radius_range(center, radius):
    return range(center - radius, center + radius + 1)


@register.filter
def neq(left, right):
    return left != right


@register.filter
def absolute(number):
    return abs(number)


@register.simple_tag
def qr(transaction):
    return (
        f"http://api.paylibo.com/paylibo/generator/czech/image"
        f"?currency=CZK"
        f"&accountNumber={settings.FIO_ACCOUNT_NUMBER}"
        f"&bankCode={settings.FIO_BANK_NUMBER}"
        f"&amount={abs(transaction.amount)}"
        f"&vs={transaction.pk}"
    )


@register.simple_tag
def link_to_admin_email(link_text=None):
    if not link_text:
        link_text = settings.ADMIN_EMAIL

    return mark_safe(f"<a href='mailto:{settings.ADMIN_EMAIL}'>{link_text}</a>")


@register.simple_tag
def indentation_by_level(level):
    return "—" * level + " "
