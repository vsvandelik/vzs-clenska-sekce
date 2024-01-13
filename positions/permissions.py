from one_time_events.models import OneTimeEvent
from trainings.models import Training
from users.permissions import PermissionRequiredMixin


class PositionPermissionMixin(PermissionRequiredMixin):
    """
    Permits users who manage any event category.
    """

    permissions_formula = [
        [OneTimeEvent.Category.COMMERCIAL],
        [OneTimeEvent.Category.COURSE],
        [OneTimeEvent.Category.PRESENTATION],
        [OneTimeEvent.Category.FOR_CHILDREN],
        [OneTimeEvent.Category.SOCIAL],
        [Training.Category.CLIMBING],
        [Training.Category.SWIMMING],
        [Training.Category.MEDICAL],
    ]
