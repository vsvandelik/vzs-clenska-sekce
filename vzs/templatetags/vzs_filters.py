import re

from django import template
from django.template.base import Node
from django.template.defaulttags import url, URLNode
from django.urls import resolve
from django.utils.safestring import mark_safe

from one_time_events.models import OneTimeEvent
from trainings.models import Training
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


@register.filter
def event_type_display_value(value):
    if value in Training.Category.values:
        return "trénink - " + Training.Category(value).label
    elif value in OneTimeEvent.Category.values:
        return "jednorázová akce - " + OneTimeEvent.Category(value).label

    return value


@register.simple_tag
def link_to_admin_email(link_text=None):
    if not link_text:
        link_text = settings.ADMIN_EMAIL

    return mark_safe(f"<a href='mailto:{settings.ADMIN_EMAIL}'>{link_text}</a>")


@register.filter
def negate(value):
    return -value


@register.simple_tag
def indentation_by_level(level):
    return "—" * level + " "


numeric_test = re.compile("^\d+$")


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
def atoi(value):
    return int(value)


@register.filter
def join(separator, iterable):
    return separator.join(iterable)


@register.filter
def handle_missing(value):
    if value in [None, ""]:
        return mark_safe(settings.VALUE_MISSING_HTML)
    return value


@register.filter
def display_presence(value):
    if value in [None, "", False]:
        return mark_safe(settings.VALUE_MISSING_HTML)
    return mark_safe(settings.VALUE_PRESENT_HTML)


class _PermURLContextVariable:
    def __init__(self, url, permitted):
        self.url = url
        self.permitted = permitted

    def __bool__(self):
        return self.permitted


class _PermURLNode(URLNode):
    def __init__(self, url_node):
        super().__init__(
            url_node.view_name, url_node.args, url_node.kwargs, url_node.asvar
        )

    def render(self, context):
        super().render(context)

        if not self.asvar:
            return ""

        url = context[self.asvar]

        match = resolve(url)

        permitted = match.func.view_class.view_has_permission(
            context["user"], **match.kwargs
        )

        context[self.asvar] = _PermURLContextVariable(url, permitted)

        return ""


@register.tag
def perm_url(parser, token):
    return _PermURLNode(url(parser, token))


class _IfPermNode(Node):
    def __init__(self, nodelist, node):
        self.nodelist = nodelist
        self.node = node

    def render(self, context):
        asvar = self.node.asvar or "perm"

        self.node.asvar = "var"
        var = context.get(self.node.asvar)
        self.node.render(context)
        perm = context[self.node.asvar]
        if var is not None:
            context[self.node.asvar] = var

        if not perm.permitted:
            return ""

        with context.push(perm=perm):
            return self.nodelist.render(context)


@register.tag
def ifperm(parser, token):
    nodelist = parser.parse(("endifperm",))
    parser.next_token()
    return _IfPermNode(nodelist, perm_url(parser, token))
