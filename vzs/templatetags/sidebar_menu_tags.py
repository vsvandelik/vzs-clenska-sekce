from django import template
from django.utils.safestring import mark_safe

from vzs.menu_render import MenuItem

register = template.Library()

MENU_STRUCTURE = [
    MenuItem("Dashboard", "pages:home", icon="fas fa-home"),
    MenuItem(
        "Osoby",
        icon="fas fa-users",
        children=[
            MenuItem("Seznam osob", "persons:index"),
            MenuItem("Skupiny", "groups:index"),
            MenuItem("Kvalifikace", "qualifications:index"),
            MenuItem("Oprávnění", "permissions:index"),
            MenuItem("Vybavení", "equipments:index"),
        ],
    ),
]


@register.simple_tag(takes_context=True)
def render_menu(context):
    output = []

    for item in MENU_STRUCTURE:
        output.append(item.render(context))

    return mark_safe("".join(output))
