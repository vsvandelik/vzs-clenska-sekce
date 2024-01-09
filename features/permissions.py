from features.models import FeatureTypeTexts
from users.permissions import PermissionRequiredMixin


class FeaturePermissionMixin(PermissionRequiredMixin):
    """
    Permits users with the correct feature permission.
    """

    @classmethod
    def view_has_permission(cls, method, active_user, feature_type, **kwargs):
        return active_user.has_perm(FeatureTypeTexts[feature_type].shortcut)
