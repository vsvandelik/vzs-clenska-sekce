from users.permissions import PermissionRequiredMixin


class PositionPermissionMixin(PermissionRequiredMixin):
    permissions_formula = [
        ["komercni_udalosti"],
        ["kurzy"],
        ["prezentacni_udalosti"],
        ["udalosti_pro_deti"],
        ["spolecenske_udalosti"],
        ["lezecke_treninky"],
        ["plavecke_treninky"],
        ["zdravoveda"],
    ]
