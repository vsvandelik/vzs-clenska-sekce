from django import template

register = template.Library()


@register.filter
def occurrence_position_assignment_organizers(occurrence, position_assignment):
    return occurrence.position_organizers(position_assignment)
