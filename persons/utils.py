from typing import Annotated, TypedDict

from django.db.models import Q
from django.shortcuts import redirect

from events.models import Event
from features.models import Feature, FeatureAssignment


class PersonsFilter(TypedDict, total=False):
    """
    Filters persons based on field filters.

    Use with :func:`vzs.utils.filter_queryset`.
    """

    name: Annotated[
        str,
        lambda name: Q(first_name__icontains=name) | Q(last_name__icontains=name),
    ]
    email: Annotated[str, lambda email: Q(email__icontains=email)]
    qualification: Annotated[
        str,
        lambda qualification: Q(
            featureassignment__feature__feature_type=Feature.Type.QUALIFICATION.value
        )
        & Q(featureassignment__feature__id=qualification),
    ]
    permission: Annotated[
        str,
        lambda permission: Q(
            featureassignment__feature__feature_type=Feature.Type.PERMISSION.value
        )
        & Q(featureassignment__feature__id=permission),
    ]
    equipment: Annotated[
        str,
        lambda equipment: Q(
            featureassignment__feature__feature_type=Feature.Type.EQUIPMENT.value
        )
        & Q(featureassignment__feature__id=equipment),
    ]
    person_type: Annotated[str, lambda person_type: Q(person_type=person_type)]
    age_from: Annotated[str, lambda age_from: Q(age__gte=age_from)]
    age_to: Annotated[str, lambda age_to: Q(age__lte=age_to)]
    event_id: Annotated[
        str,
        lambda event_id: Q(
            id__in=[
                p.pk for p in Event.objects.get(pk=event_id).approved_participants()
            ]
        ),
    ]


def send_email_to_selected_persons(selected_persons):
    recipients = []
    for person in selected_persons:
        if person.email is not None:
            recipients.append(
                f"{person.first_name} {person.last_name} <{person.email}>"
            )

        persons_managing = person.managed_by.all()
        for person_managing in persons_managing:
            if person_managing.email is not None:
                recipients.append(
                    f"{person_managing.first_name} {person_managing.last_name} <{person_managing.email}>"
                )

    gmail_link = "https://mail.google.com/mail/?view=cm&to=" + ",".join(recipients)

    return redirect(gmail_link)


def extend_kwargs_of_assignment_features(person, kwargs):
    kwargs.setdefault(
        "qualifications",
        FeatureAssignment.objects.filter(
            person=person, feature__feature_type=Feature.Type.QUALIFICATION.value
        ),
    )

    kwargs.setdefault(
        "permissions",
        FeatureAssignment.objects.filter(
            person=person, feature__feature_type=Feature.Type.PERMISSION.value
        ),
    )

    kwargs.setdefault(
        "equipments",
        FeatureAssignment.objects.filter(
            person=person,
            feature__feature_type=Feature.Type.EQUIPMENT.value,
            date_returned__isnull=True,
        ),
    )
