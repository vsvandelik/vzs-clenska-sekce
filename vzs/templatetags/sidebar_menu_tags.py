from django import template
from django.utils.safestring import mark_safe

from one_time_events.views import OneTimeEventAdminListView
from trainings.views import TrainingAdminListView
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
        get_one_time_events_menu_item(context),
        get_trainings_menu_item(context),
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
                MenuItem("Export podkladů", "transactions:accounting-export"),
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
        MenuItem("Kontakty", "pages:detail kontakty", icon="fas fa-envelope"),
    ]

    output = []

    for item in menu_structure:
        output.append(item.render(context))

    return mark_safe("".join(output))


def get_one_time_events_menu_item(context):
    can_person_edit_one_time_events = (
        OneTimeEventAdminListView.view_has_permission_person(
            "GET", context["active_person"], POST={}
        )
    )

    if can_person_edit_one_time_events:
        return MenuItem(
            "Akce",
            icon="fas fa-calendar",
            children=[
                MenuItem("Moje akce", "one_time_events:index"),
                MenuItem("Všechny akce", "one_time_events:list-admin"),
            ],
        )

    else:
        return MenuItem("Akce", "one_time_events:index", icon="fas fa-calendar")


def get_trainings_menu_item(context):
    can_person_edit_trainings = TrainingAdminListView.view_has_permission_person(
        "GET", context["active_person"], POST={}
    )

    if can_person_edit_trainings:
        return MenuItem(
            "Tréninky",
            icon="fas fa-dumbbell",
            children=[
                MenuItem("Moje tréninky", "trainings:index"),
                MenuItem("Všechny tréninky", "trainings:list-admin"),
            ],
        )

    else:
        return MenuItem("Tréninky", "trainings:index", icon="fas fa-dumbbell")
