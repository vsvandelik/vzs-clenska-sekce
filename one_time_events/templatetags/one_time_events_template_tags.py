import urllib

from django import template
from django.db.models import Q

from vzs.settings import GOOGLE_MAPS_API_KEY

register = template.Library()


@register.filter
def occurrence_person_2_organizer_assignment(occurrence, person):
    assignment = occurrence.organizers_assignments_by_Q(Q(person=person))
    if assignment.count() == 1:
        return assignment[0]
    return None


@register.filter
def as_google_map_src(location):
    encoded_location = urllib.parse.quote_plus(location)
    return f"https://www.google.com/maps/embed/v1/place?key={GOOGLE_MAPS_API_KEY}&q={encoded_location}"
