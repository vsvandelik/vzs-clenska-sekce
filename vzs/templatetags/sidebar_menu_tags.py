from django import template
from django.utils.safestring import mark_safe

from vzs.menu_render import MenuItem

register = template.Library()


@register.simple_tag(takes_context=True)
def render_menu(context):
    menu_structure = [
        MenuItem("Dashboard", "pages:home", icon="fas fa-home"),
        MenuItem(
            context["active_person"],
            icon="fas fa-user",
            children=[
                MenuItem("Profil", "my-profile:index"),
                MenuItem("Transakce", "my-transactions"),
            ],
        ),
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

    output = []

    for item in menu_structure:
        output.append(item.render(context))

    return mark_safe("".join(output))
