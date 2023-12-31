from django.http import HttpRequest

from users.permissions import PermissionRequiredMixin


class TransactionEditPermissionMixin(PermissionRequiredMixin):
    """
    Permits users with the ``users.transakce`` permission.
    """

    permissions_formula = [["transakce"]]
    """:meta private:"""


class TransactionDisableEditSettledPermissionMixin(TransactionEditPermissionMixin):
    """
    Permits users with the ``users.transakce`` permission
    to edit transactions that are not settled.
    """

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        """:meta private:"""

        self.object = self.get_object()

        if self.object.is_settled:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    # TODO: promyslet, jestli by se dala nejak prepsat metoda view_has_permission, tak,
    # aby se dalo pouzit iferm na zjisteni, jestli je transakce settled, a pokud je,
    # tak se ifperm vyhodnoti jako false
