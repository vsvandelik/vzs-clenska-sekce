from django import template

register = template.Library()


@register.filter
def can_enroll_position(occurrence_person, position_assignment):
    occurrence, person = occurrence_person
    return occurrence.can_enroll_position(person, position_assignment)


@register.filter
def can_unenroll_position(occurrence_person, position_assignment):
    occurrence, person = occurrence_person
    return occurrence.can_unenroll_position(person, position_assignment)


@register.filter
def get_organizer_assignment(occurrence_person, position_assignment):
    occurrence, person = occurrence_person
    return occurrence.get_organizer_assignment(person, position_assignment)
