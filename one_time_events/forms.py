from django.forms import ModelForm
from django_select2.forms import Select2Widget

from vzs.widgets import DatePickerWithIcon
from .models import OneTimeEvent
from events.models import EventOrOccurrenceState


class OneTimeEventForm(ModelForm):
    class Meta:
        model = OneTimeEvent
        fields = [
            "name",
            "description",
            "location",
            "capacity",
            "category",
            "date_start",
            "date_end",
            "default_participation_fee",
        ]
        widgets = {
            "category": Select2Widget(),
            "date_start": DatePickerWithIcon(attrs={"onchange": "dateChanged()"}),
            "date_end": DatePickerWithIcon(attrs={"onchange": "dateChanged()"}),
        }

    def _check_date_constraints(self):
        if self.cleaned_data["date_start"] >= self.cleaned_data["date_end"]:
            self.add_error(
                "date_end", "Konec události nesmí být dříve než její začátek"
            )

    def clean(self):
        cleaned_data = super().clean()
        self._check_date_constraints()
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        if self.instance.id is None:
            instance.state = EventOrOccurrenceState.OPEN
        if commit:
            instance.save()
        return instance
