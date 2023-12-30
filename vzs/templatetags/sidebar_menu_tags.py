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
        MenuItem("Akce", "one_time_events:index", icon="fas fa-calendar"),
        MenuItem("Tréninky", "trainings:index", icon="fas fa-dumbbell"),
        MenuItem(
            "Správa událostí",
            icon="fab fa-elementor",
            children=[
                MenuItem("Pozice", "positions:index"),
            ],
        ),
        MenuItem(
            "Transakce",
            icon="fas fa-dollar-sign",
            children=[
                MenuItem("Seznam transakcí", "transactions:index"),
                MenuItem("Hromadné transakce", "transactions:index-bulk"),
                MenuItem("Účetní podklady", "transactions:accounting-export"),
            ],
        ),
        MenuItem(
            "Nastavení",
            icon="fas fa-cogs",
            children=[
                MenuItem("Seznam API tokenů", "api:token:index"),
            ],
        ),
        MenuItem("Nápověda", "pages:detail napoveda", icon="fas fa-question-circle"),
        MenuItem("Kontakt", "pages:detail kontakt", icon="fas fa-envelope"),
    ]

    output = []

    for item in menu_structure:
        output.append(item.render(context))

    return mark_safe("".join(output))
