from typing import Annotated, TypedDict

from django.db.models import Q


class PersonExistsFilter(TypedDict, total=False):
    """
    Filters persons with the given first and last name.

    Use with :func:`vzs.utils.filter_queryset`.
    """

    first_name: Annotated[str, lambda first_name: Q(first_name=first_name)]
    last_name: Annotated[str, lambda last_name: Q(last_name=last_name)]
