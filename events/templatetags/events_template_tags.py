from django import template

register = template.Library()


@register.filter
def occurrence_position_assignment_organizers(occurrence, position_assignment):
    return occurrence.position_organizers(position_assignment)


@register.filter
def can_enroll_position(occurrence_and_person, position_assignment):
    occurrence, person = occurrence_and_person
    return occurrence.can_enroll_position(person, position_assignment)


@register.filter
def can_unenroll_position(occurrence_and_person, position_assignment):
    occurrence, person = occurrence_and_person
    return occurrence.can_unenroll_position(person, position_assignment)


@register.filter
def get_organizer_assignment(occurrence_and_person, position_assignment):
    occurrence, person = occurrence_and_person
    return occurrence.get_organizer_assignment(person, position_assignment)


@register.filter
def participant_enrollment_2_attendance(participant_enrollment, occurrence):
    return participant_enrollment.participant_attendance(occurrence)


@register.simple_tag
def display_date_range(event):
    if event.date_start == event.date_end:
        return event.date_start.strftime("%d. %m. %Y")
    else:
        return "%s - %s" % (
            event.date_start.strftime("%d. %m. %Y"),
            event.date_end.strftime("%d. %m. %Y"),
        )
