from datetime import datetime, timedelta, timezone

from django import forms
from django.forms import Form, ModelForm, MultipleChoiceField
from django.forms.widgets import CheckboxInput
from django.utils import timezone
from django_select2.forms import Select2Widget

from persons.models import Person
from vzs.widgets import DateTimePickerWithIcon, DatePickerWithIcon, TimePickerWithIcon
from .models import Event, EventPositionAssignment
from positions.models import EventPosition
from positions.forms import GroupMembershipForm as PositionsGroupMembershipForm

#
#
# class AddDeleteParticipantFromOneTimeEventForm(Form):
#     person_id = forms.IntegerField()
#
#     def __init__(self, *args, **kwargs):
#         self._event_id = kwargs.pop("event_id")
#         super().__init__(*args, **kwargs)
#
#     def clean(self):
#         cleaned_data = super().clean()
#         pid = cleaned_data["person_id"]
#         cleaned_data["event_id"] = self._event_id
#         eid = cleaned_data["event_id"]
#         try:
#             cleaned_data["person"] = Person.objects.get(pk=pid)
#             cleaned_data["event"] = Event.objects.get(pk=eid)
#             event = cleaned_data["event"]
#             event.set_type()
#             if not event.is_one_time_event:
#                 self.add_error("event_id", "Událost {event} není jednorázovou událostí")
#             if event.state in [
#                 Event.State.APPROVED,
#                 Event.State.FINISHED,
#             ]:
#                 self.add_error(
#                     "event_id",
#                     f"Událost {event} je uzavřena nebo schválena",
#                 )
#         except Person.DoesNotExist:
#             self.add_error("person_id", f"Osoba s id {pid} neexistuje")
#         except Event.DoesNotExist:
#             self.add_error("event_id", f"Událost s id {eid} neexistuje")
#         return cleaned_data
#
#
# class EventPositionAssignmentForm(ModelForm):
#     class Meta:
#         model = EventPositionAssignment
#         fields = [
#             "position",
#             "count",
#         ]
#         labels = {"position": "Pozice"}
#         widgets = {
#             "position": Select2Widget(attrs={"onchange": "positionChanged(this)"})
#         }
#
#     def __init__(self, *args, **kwargs):
#         self.event = kwargs.pop("event")
#         self.position = kwargs.pop("position", None)
#         super().__init__(*args, **kwargs)
#         self.fields["count"].widget.attrs["min"] = 1
#         if self.position is not None:
#             self.fields["position"].widget.attrs["disabled"] = True
#         else:
#             self.fields["position"].queryset = EventPosition.objects.filter(
#                 pk__in=EventPosition.objects.all()
#                 .values_list("pk", flat=True)
#                 .difference(
#                     EventPositionAssignment.objects.filter(
#                         event=self.event
#                     ).values_list("position_id", flat=True)
#                 )
#             )
#
#     def save(self, commit=True):
#         instance = super().save(False)
#         if self.instance.id is None:
#             instance.event = self.event
#         else:
#             instance.position = self.position
#         if commit:
#             instance.save()
#
#
# class MinAgeForm(ModelForm):
#     class Meta:
#         model = Event
#         fields = ["min_age_enabled", "min_age"]
#         labels = {
#             "min_age_enabled": "Vyžadována",
#             "min_age": "Minimální věková hranice",
#         }
#         widgets = {
#             "min_age_enabled": CheckboxInput(
#                 attrs={"onchange": "minAgeCheckboxClicked(this)"}
#             )
#         }
#
#     def clean(self):
#         cleaned_data = super().clean()
#         min_age_enabled = cleaned_data["min_age_enabled"]
#         if not min_age_enabled:
#             cleaned_data["min_age"] = self.instance.min_age
#         if min_age_enabled:
#             if "min_age" not in cleaned_data or cleaned_data["min_age"] is None:
#                 self.add_error("min_age", "Toto pole je nutné vyplnit")
#         return cleaned_data
#
#
# class GroupMembershipForm(PositionsGroupMembershipForm):
#     class Meta:
#         model = Event
#         fields = ["group_membership_required", "group"]
#         labels = {"group_membership_required": "Vyžadováno", "group": "Skupina"}
#         widgets = {
#             "group_membership_required": CheckboxInput(
#                 attrs={"onchange": "groupMembershipRequiredClicked(this)"}
#             ),
#             "group": Select2Widget(attrs={"onchange": "groupChanged(this)"}),
#         }
#
#
# class PersonTypeEventForm(Form):
#     person_type = forms.ChoiceField(choices=Person.Type.choices)
#
#     def __init__(self, *args, **kwargs):
#         self._event_id = kwargs.pop("event_id")
#         super().__init__(*args, **kwargs)
#
#     def clean(self):
#         cleaned_data = super().clean()
#         cleaned_data["event_id"] = self._event_id
#         eid = cleaned_data["event_id"]
#         try:
#             cleaned_data["event"] = Event.objects.get(pk=eid)
#         except EventPosition.DoesNotExist:
#             self.add_error("event_id", f"Událost s id {eid} neexistuje")
#
#         return cleaned_data
