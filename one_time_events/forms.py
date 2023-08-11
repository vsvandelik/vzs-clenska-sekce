from datetime import datetime, timedelta, timezone

from django import forms
from django.forms import Form, ModelForm, MultipleChoiceField
from django.forms.widgets import CheckboxInput
from django.utils import timezone
from django_select2.forms import Select2Widget

from persons.models import Person
from vzs.widgets import DateTimePickerWithIcon, DatePickerWithIcon, TimePickerWithIcon
from .models import OneTimeEvent


class OneTimeEventForm(ModelForm):
    class Meta:
        model = OneTimeEvent
        fields = [
            "name",
            "description",
            "location",
            "capacity",
            "category",
            "default_participation_fee",
        ]
        widgets = {"category": Select2Widget()}
        # widgets = {
        #     "time_start": DateTimePickerWithIcon(
        #         attrs={"onchange": "dateChanged()"},
        #     ),
        #     "time_end": DateTimePickerWithIcon(attrs={"onchange": "dateChanged()"})
        # }

    # def _check_date_constraints(self):
    #     if self.cleaned_data["time_start"] >= self.cleaned_data["time_end"]:
    #         self.add_error(
    #             "time_end", "Konec události nesmí být dříve než její začátek"
    #         )

    def clean(self):
        cleaned_data = super().clean()
        # self._check_date_constraints()
        return cleaned_data
