from django import template
from django.db.models import Q

register = template.Library()


@register.filter
def occurrence_person_2_organizer_assignment(occurrence, person):
    assignment = occurrence.organizers_assignments_by_Q(Q(person=person))
    if assignment.count() == 1:
        return assignment[0]
    return None
