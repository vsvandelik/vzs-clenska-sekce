import datetime
from dateutil.parser import parse

from django.forms import ModelForm, MultipleChoiceField
from django import forms
from .models import Event
from .utils import weekday_2_day_shortcut

trainings_per_week_choices = (("1", "1x"), ("2", "2x"), ("3", "3x"))


class MultipleChoiceFieldNoValidation(MultipleChoiceField):
    def validate(self, value):
        pass


class TrainingForm(ModelForm):
    starts_date = forms.DateField()
    ends_date = forms.DateField()
    trainings_per_week = forms.ChoiceField(choices=trainings_per_week_choices)

    po = forms.BooleanField(label_suffix="Po", required=False)
    from_po = forms.TimeField(required=False)
    to_po = forms.TimeField(required=False)

    ut = forms.BooleanField(label_suffix="Út", required=False)
    from_ut = forms.TimeField(required=False)
    to_ut = forms.TimeField(required=False)

    st = forms.BooleanField(label_suffix="St", required=False)
    from_st = forms.TimeField(required=False)
    to_st = forms.TimeField(required=False)

    ct = forms.BooleanField(label_suffix="Čt", required=False)
    from_ct = forms.TimeField(required=False)
    to_ct = forms.TimeField(required=False)

    pa = forms.BooleanField(label_suffix="Pá", required=False)
    from_pa = forms.TimeField(required=False)
    to_pa = forms.TimeField(required=False)

    so = forms.BooleanField(label_suffix="So", required=False)
    from_so = forms.TimeField(required=False)
    to_so = forms.TimeField(required=False)

    ne = forms.BooleanField(label_suffix="Ne", required=False)
    from_ne = forms.TimeField(required=False)
    to_ne = forms.TimeField(required=False)

    day = MultipleChoiceFieldNoValidation(widget=forms.CheckboxSelectMultiple)

    def _factory(self):
        event_instance = Event.objects.create()
        event_instance.name = self["name"].data
        event_instance.description = self["description"].data
        event_instance.capacity = self["capacity"].data
        event_instance.age_limit = self["age_limit"].data
        event_instance.state = Event.State.FUTURE
        return event_instance

    def save(self, **kwargs):
        parent_training_instance = self._factory()
        parent_training_instance.time_start = parse(self["starts_date"].data)
        parent_training_instance.time_end = parse(self["ends_date"].data)
        parent_training_instance.save()

        for date_raw in self["day"].data:
            date = datetime.datetime.strptime(date_raw, "%d.%m.%Y")
            day_short = weekday_2_day_shortcut(date.weekday())
            hour_start, minute_start = [
                int(v) for v in self[f"from_{day_short}"].data.split(":")
            ]
            hour_end, minute_end = [
                int(v) for v in self[f"to_{day_short}"].data.split(":")
            ]
            date_start = datetime.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=hour_start,
                minute=minute_start,
            )
            date_end = datetime.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=hour_end,
                minute=minute_end,
            )
            child_training = self._factory()
            child_training.time_start = date_start
            child_training.time_end = date_end
            child_training.parent = parent_training_instance
            child_training.save()

    class Meta:
        model = Event
        fields = ["name", "description", "capacity", "age_limit"]
