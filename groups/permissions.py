from users.permissions import PermissionRequiredMixin


class GroupPermissionMixin(PermissionRequiredMixin):
    """
    Permits users with the ``skupiny`` permission.
    """

    permissions_formula = [["skupiny"]]
