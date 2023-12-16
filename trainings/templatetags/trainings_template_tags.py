from django import template

from ..models import TrainingParticipantAttendance, TrainingAttendance
from ..utils import day_shortcut_2_weekday as day_shortcut_2_weekday_impl
from ..utils import day_shortcut_pretty as day_shortcut_pretty_impl
from ..utils import weekday_2_day_shortcut as weekday_2_day_shortcut_impl
from ..utils import weekday_pretty as weekday_pretty_impl

register = template.Library()

attendance_status_color_map = {
    TrainingAttendance.PRESENT: "success",
    TrainingAttendance.EXCUSED: "warning",
    TrainingAttendance.UNEXCUSED: "danger",
    "not_closed": "secondary",
}


@register.filter
def day_shortcut_2_weekday(value):
    return day_shortcut_2_weekday_impl(value)


@register.filter
def weekday_2_day_shortcut(value):
    return weekday_2_day_shortcut_impl(value)


@register.filter
def day_shortcut_pretty(value):
    return day_shortcut_pretty_impl(value)


@register.filter
def weekday_pretty(value):
    return weekday_pretty_impl(value)


@register.filter
def get_weekday(date_or_datetime):
    return date_or_datetime.weekday()


@register.filter
def approved_enrollments_by_weekday(training, weekday):
    return training.approved_enrollments_by_weekday(weekday)


@register.filter
def substitute_enrollments_by_weekday(training, weekday):
    return training.substitute_enrollments_by_weekday(weekday)


@register.filter
def coach_position_assignment_coaches(training, position_assignment):
    return training.position_coaches(position_assignment)


@register.filter
def occurrence_position_assignment_present_coaches(occurrence, position_assignment):
    return occurrence.position_present_coaches_assignments(position_assignment)


@register.filter
def get_participant_attendance(occurrence, person):
    return TrainingParticipantAttendance.objects.get(
        occurrence=occurrence, person=person
    )


@register.filter
def get_coach_attendance(coach_assignment, occurrence):
    return coach_assignment.coach_attendance(occurrence)


@register.filter
def get_color_by_attendance_status(attendance_status):
    return attendance_status_color_map[attendance_status]
