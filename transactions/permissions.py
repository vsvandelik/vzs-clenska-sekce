from django.http import HttpRequest

from transactions.models import Transaction
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

    @classmethod
    def view_has_permission(cls, method: str, active_user, pk, **kwargs):
        transaction = Transaction.objects.filter(pk=pk).first()

        if transaction is None:
            return False

        if transaction.is_settled:
            return False

        return super().view_has_permission(method, active_user, pk=pk, **kwargs)
