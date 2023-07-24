from features.models import Feature, FeatureAssignment
from persons.models import Person

from django.db.models import Q
from django.shortcuts import redirect

import csv


def parse_persons_filter_queryset(params_dict, persons):
    name = params_dict.get("name")
    email = params_dict.get("email")
    qualification = params_dict.get("qualifications")
    permission = params_dict.get("permissions")
    equipment = params_dict.get("equipments")
    person_type = params_dict.get("person_type")
    age_from = params_dict.get("age_from")
    age_to = params_dict.get("age_to")

    if name:
        persons = persons.filter(
            Q(first_name__icontains=name) | Q(last_name__icontains=name)
        )

    if email:
        persons = persons.filter(email__icontains=email)

    if qualification:
        persons = persons.filter(
            featureassignment__feature__feature_type=Feature.Type.QUALIFICATION.value,
            featureassignment__feature__id=qualification,
        )

    if permission:
        persons = persons.filter(
            featureassignment__feature__feature_type=Feature.Type.PERMISSION.value,
            featureassignment__feature__id=permission,
        )

    if equipment:
        persons = persons.filter(
            featureassignment__feature__feature_type=Feature.Type.EQUIPMENT.value,
            featureassignment__feature__id=equipment,
        )

    if person_type:
        persons = persons.filter(person_type=person_type)

    if age_from:
        persons = persons.filter(age__gte=age_from)

    if age_to:
        persons = persons.filter(age__lte=age_to)

    return persons.order_by("last_name")


def send_email_to_selected_persons(selected_persons):
    recipients = [f"{p.first_name} {p.last_name} <{p.email}>" for p in selected_persons]

    gmail_link = "https://mail.google.com/mail/?view=cm&to=" + ",".join(recipients)

    return redirect(gmail_link)


def extend_kwargs_of_assignment_features(person_id, kwargs):
    kwargs.setdefault(
        "qualifications",
        FeatureAssignment.objects.filter(
            person=person_id,
            feature__feature_type=Feature.Type.QUALIFICATION.value,
        ),
    )

    kwargs.setdefault(
        "permissions",
        FeatureAssignment.objects.filter(
            person=person_id,
            feature__feature_type=Feature.Type.PERMISSION.value,
        ),
    )

    kwargs.setdefault(
        "equipments",
        FeatureAssignment.objects.filter(
            person=person_id,
            feature__feature_type=Feature.Type.EQUIPMENT.value,
        ),
    )
