from django.forms import ModelForm, CheckboxSelectMultiple
from django_select2.forms import Select2Widget

from vzs.widgets import DatePickerWithIcon
from .models import OneTimeEvent, OneTimeEventOccurrence
from events.models import EventOrOccurrenceState
from events.forms import MultipleChoiceFieldNoValidation
from events.utils import parse_czech_date
from .utils import index_no_except


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

        children = instance.sorted_occurrences_list()
        occurrences = self.cleaned_data["occurrences"]
        i = 0
        while i < len(occurrences):
            date, hours = occurrences[i]
            child = self._find_child_with_date(children, date)
            if child is not None:
                if hours != child.hours:
                    child.hours = hours
                    child.save()
                del occurrences[i]
                i -= 1
            i += 1

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

    def _find_child_with_date(self, children, date):
        for child in children:
            if child.date == date:
                return child
        return None
