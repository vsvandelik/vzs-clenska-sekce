import re

from django import template
from django.template.base import Node
from django.template.defaultfilters import stringfilter
from django.template.defaulttags import URLNode, url
from django.template.exceptions import TemplateSyntaxError
from django.urls import resolve
from django.utils import formats
from django.utils.safestring import mark_safe

from one_time_events.models import OneTimeEvent
from trainings.models import Training
from vzs import settings
from vzs.utils import qr as utils_qr

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
    return utils_qr(transaction)


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


numeric_test = re.compile(r"^\d+$")


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
    try:
        return indexable[i]
    except (ValueError, IndexError, KeyError):
        return None


@register.filter
def atoi(value):
    return int(value)


@register.filter
def join(separator, iterable):
    return separator.join(iterable)


@register.filter
def handle_missing(value):
    if value in [None, "", "None Kč"]:
        return mark_safe(settings.VALUE_MISSING_HTML)
    return value


@register.filter
def handle_missing_empty(value):
    if value in [None, "", "None Kč"]:
        return ""
    return value


@register.filter
def display_presence(value):
    if value in [None, "", False]:
        return mark_safe(settings.VALUE_MISSING_HTML)
    return mark_safe(settings.VALUE_PRESENT_HTML)


@register.filter(expects_localtime=True)
def datetime(value):
    if value in [None, ""]:
        return ""
    return formats.date_format(value, settings.cs_formats.DATETIME_FORMAT)


@register.filter(expects_localtime=True)
def datetime_precise(value):
    if value in [None, ""]:
        return ""
    return formats.date_format(value, settings.DATETIME_PRECISE_FORMAT)


@register.filter
def ge(a, b):
    return a >= b


@register.filter
def subtract(a, b):
    return a - b


@register.filter
def math_max(a, b):
    return max(a, b)


@register.filter
def money(value):
    return f"{value} Kč"


@register.simple_tag
def value_present_symbol():
    return mark_safe(settings.VALUE_PRESENT_HTML)


@register.simple_tag
def value_missing_symbol():
    return mark_safe(settings.VALUE_MISSING_HTML)


@register.filter
def tuple(a, b):
    return a, b


@register.filter(name="range")
def filter_range(start, end):
    return range(start, end)


class _PermURLContextVariable:
    def __init__(self, url, permitted):
        self.url = url
        self.permitted = permitted

    def __bool__(self):
        return self.permitted


class _PermURLNode(URLNode):
    def __init__(self, url_node):
        if url_node.asvar is None:
            raise TemplateSyntaxError(
                "Permission template tags require an `as` variable name."
            )

        url_kwargs = {}
        self.permission_kwargs = {}

        for key, value in url_node.kwargs.items():
            if key.startswith("permission_"):
                self.permission_kwargs[key] = value
            else:
                url_kwargs[key] = value

        super().__init__(url_node.view_name, url_node.args, url_kwargs, url_node.asvar)

    def render(self, context):
        super().render(context)

        url = context[self.asvar]

        match = resolve(url)

        permission_kwargs = {
            key: value.resolve(context) for key, value in self.permission_kwargs.items()
        }

        permitted = match.func.view_class.view_has_permission_person(
            context["active_person"], **self.kwargs, **permission_kwargs
        )

        context[self.asvar] = _PermURLContextVariable(url, permitted)

        return ""


@register.tag
def perm_url(parser, token):
    return _PermURLNode(url(parser, token))


class _IfPermNode(Node):
    def __init__(self, nodelist, perm_url_node):
        self.nodelist = nodelist
        self.perm_url_node = perm_url_node

    def render(self, context):
        with context.push():
            self.perm_url_node.render(context)
            perm = context[self.perm_url_node.asvar]

        if not perm.permitted:
            return ""

        with context.push(**{self.perm_url_node.asvar: perm}):
            return self.nodelist.render(context)


@register.tag
def ifperm(parser, token):
    nodelist = parser.parse(("endifperm",))
    parser.next_token()
    return _IfPermNode(nodelist, perm_url(parser, token))


@register.filter
@stringfilter
def suffix_not_empty(value, args):
    return value + str(args) if value else value
