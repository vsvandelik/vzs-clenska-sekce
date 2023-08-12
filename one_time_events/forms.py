from django.forms import ModelForm
from django_select2.forms import Select2Widget

from vzs.widgets import DatePickerWithIcon
from .models import OneTimeEvent
from events.models import EventOrOccurrenceState
from events.utils import parse_czech_date


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

    def __init__(self, *args, **kwargs):
        self.POST = kwargs.pop("request").POST
        super().__init__(*args, **kwargs)

    def _check_date_constraints(self):
        if self.cleaned_data["date_start"] >= self.cleaned_data["date_end"]:
            self.add_error(
                "date_end", "Konec události nesmí být dříve než její začátek"
            )

    def _add_validate_occurrences(self):
        occurrences = []
        for attr_name in self.POST:
            if attr_name[0].isdigit() and "_checkbox" in attr_name:
                date_raw, _ = attr_name.split("_")
                date_valid, date = self._check_occurrence_date(date_raw)
                if date_valid:
                    hours_valid, hours = self._check_hours(date_raw)
                    if hours_valid:
                        occurrences.append((date, hours))
        self.cleaned_data["occurrences"] = occurrences

    def _check_hours(self, date_raw):
        key = f"{date_raw}_hours"
        if key in self.POST:
            value = self.POST[key]
            if value.isdigit() and 1 <= int(value) <= 10:
                return True, int(value)
        self.add_error(None, f"Neplatná hodnota počtu hodin dne {date_raw}")
        return False, None

    def _check_occurrence_date(self, date_raw):
        try:
            date = parse_czech_date(date_raw).date()
        except:
            self.add_error(None, "Neplatný datum konání tréninku")
            return False, None

        if (
            date < self.cleaned_data["date_start"]
            or date > self.cleaned_data["date_end"]
        ):
            self.add_error(None, "Datum konání tréninku je mimo rozsah konání události")
            return False, None
        return True, date

    def clean(self):
        cleaned_data = super().clean()
        self._check_date_constraints()
        self._add_validate_occurrences()
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        if self.instance.id is None:
            instance.state = EventOrOccurrenceState.OPEN
        if commit:
            instance.save()
        return instance
