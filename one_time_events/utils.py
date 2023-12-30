from datetime import date
from typing import TypedDict, Annotated

from django.db.models import Q


class OneTimeEventsFilter(TypedDict, total=False):
    """
    Defines a filter for one time events.

    Use with :func:`vzs.utils.filter_queryset`.
    """

    category: Annotated[str, lambda category: Q(category=category)]

    date_from: Annotated[date, lambda date_from: Q(date_start__gte=date_from)]

    date_to: Annotated[date, lambda date_to: Q(date_end__lte=date_to)]

    state: Annotated[str, lambda state: Q(state=state)]
