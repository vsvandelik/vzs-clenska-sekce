import datetime

from django.forms import ModelForm, CheckboxSelectMultiple
from django_select2.forms import Select2Widget

from vzs.widgets import DatePickerWithIcon
from .models import OneTimeEvent, OneTimeEventOccurrence
from events.models import EventOrOccurrenceState
from events.forms import MultipleChoiceFieldNoValidation
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

    dates = MultipleChoiceFieldNoValidation(widget=CheckboxSelectMultiple)

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
        dates = self.cleaned_data.pop("dates")
        hours = self.POST.getlist("hours")
        if len(dates) < len(hours):
            self.add_error(
                None, "Počet počtů hodin je větší počet dní, kdy se akce koná"
            )
            return
        if len(dates) > len(hours):
            self.add_error(
                None, "Počet počtů hodin menší než počet dnů, kdy se akce koná"
            )
            return
        for i in range(len(dates)):
            date_raw = dates[i]
            hours_raw = hours[i]
            date_valid, date = self._check_occurrence_date(date_raw)
            if date_valid:
                hours_valid, hour = self._check_hours(date_raw, hours_raw)
                if hours_valid:
                    occurrences.append((date, hour))
        self.cleaned_data["occurrences"] = occurrences

    def _check_hours(self, date_raw, hours_raw):
        try:
            hours = int(hours_raw)
            return 1 <= hours <= 10, hours
        except:
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

        children = instance.occurrences_list()
        occurrences = self.cleaned_data["occurrences"]
        for child in children:
            occurrence = self._find_occurrence_with_date(child.date)
            if occurrence is not None:
                if child.hours != occurrence[1]:
                    child.hours = occurrence[1]
                    child.save()
                self.cleaned_data["occurrences"].remove(occurrence)
            else:
                child.delete()

        for i in range(len(occurrences)):
            date, hours = occurrences[i]
            occurrence_obj = OneTimeEventOccurrence(
                event=instance,
                state=EventOrOccurrenceState.OPEN,
                date=date,
                hours=hours,
            )
            occurrence_obj.save()

        return instance

    def generate_dates(self):
        if (
            hasattr(self, "cleaned_data")
            and "occurrences" in self.cleaned_data
            and "date_start" in self.cleaned_data
            and "date_end" in self.cleaned_data
        ):
            cleaned_data = self.cleaned_data
            date_start = cleaned_data["date_start"]
            date_end = cleaned_data["date_end"]
            is_date_checked = self._is_date_checked_form
            date_hours = self._date_hours_form

        elif self.instance.id is not None:
            date_start = self.instance.date_start
            date_end = self.instance.date_end
            is_date_checked = self._is_date_checked_instance
            date_hours = self._date_hours_instance
        else:
            return []

        output = []
        while date_start <= date_end:
            if is_date_checked(date_start):
                hours = date_hours(date_start)
                output.append((True, date_start, hours))
            else:
                output.append((False, date_start, None))
            date_start += datetime.timedelta(days=1)
        return output

    def _find_date_hours_form(self, d):
        for date, hours in self.cleaned_data["occurrences"]:
            if d == date:
                return True, hours
        return False, None

    def _is_date_checked_form(self, d):
        checked, _ = self._find_date_hours_form(d)
        return checked

    def _date_hours_form(self, d):
        _, hours = self._find_date_hours_form(d)
        return hours

    def _find_date_hours_instance(self, d):
        for occurrence in self.instance.occurrences_list():
            if d == occurrence.date:
                return True, occurrence.hours
        return False, None

    def _is_date_checked_instance(self, d):
        checked, _ = self._find_date_hours_instance(d)
        return checked

    def _date_hours_instance(self, d):
        _, hours = self._find_date_hours_instance(d)
        return hours

    def _find_occurrence_with_date(self, d):
        for date, hours in self.cleaned_data["occurrences"]:
            if d == date:
                return date, hours
        return None
