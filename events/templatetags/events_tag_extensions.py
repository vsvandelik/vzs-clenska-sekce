from django import template

register = template.Library()


#
# @register.filter
# def event_participation(person, event):
#     return (
#         EventOccurrenceParticipation.objects.filter(event=event, person=person)
#         .all()
#         .first()
#     )
