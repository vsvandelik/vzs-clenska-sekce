from users.permissions import PermissionRequiredMixin


class PositionPermissionMixin(PermissionRequiredMixin):
    """
    Permits users who manage any event category.
    """

    permissions_formula = [
        ["komercni"],
        ["kurz"],
        ["prezentacni"],
        ["pro-deti"],
        ["spolecenska"],
        ["lezecky"],
        ["plavecky"],
        ["zdravoveda"],
    ]
