from datetime import datetime, timedelta, timezone

from django import forms
from django.forms import ModelForm
from django.utils import timezone
from django_select2.forms import Select2Widget

from events.forms import MultipleChoiceFieldNoValidation
from events.models import EventOrOccurrenceState
from trainings.utils import (
    weekday_2_day_shortcut,
    days_shortcut_list,
    day_shortcut_2_weekday,
)
from events.utils import parse_czech_date
from vzs.widgets import DatePickerWithIcon, TimePickerWithIcon
from .models import Training, TrainingOccurrence


class TrainingForm(ModelForm):
    class Meta:
        model = Training
        fields = [
            "name",
            "description",
            "location",
            "capacity",
            "date_start",
            "date_end",
            "category",
            "po_from",
            "po_to",
            "ut_from",
            "ut_to",
            "st_from",
            "st_to",
            "ct_from",
            "ct_to",
            "pa_from",
            "pa_to",
            "so_from",
            "so_to",
            "ne_from",
            "ne_to",
        ]
        widgets = {
            "category": Select2Widget(),
            "date_start": DatePickerWithIcon(attrs={"onchange": "dateChanged()"}),
            "date_end": DatePickerWithIcon(attrs={"onchange": "dateChanged()"}),
            "po_from": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "po_to": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "ut_from": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "ut_to": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "st_from": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "st_to": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "ct_from": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "ct_to": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "pa_from": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "pa_to": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "so_from": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "so_to": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "ne_from": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
            "ne_to": TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        event = kwargs["instance"]
        if event is not None:
            self.initial["date_start"] = event.date_start
            self.initial["date_end"] = event.date_end
            for weekday in event.weekdays_occurs_list():
                day_shortcut = weekday_2_day_shortcut(weekday)
                self.initial[day_shortcut] = True
            for attr, value in event.__dict__.items():
                if attr[3:] == "from" or attr[3:] == "to":
                    self.initial[attr] = value

    po = forms.BooleanField(
        label="Po",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dayToggled(this)"}),
    )
    ut = forms.BooleanField(
        label="Út",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dayToggled(this)"}),
    )
    st = forms.BooleanField(
        label="St",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dayToggled(this)"}),
    )
    ct = forms.BooleanField(
        label="Čt",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dayToggled(this)"}),
    )
    pa = forms.BooleanField(
        label="Pá",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dayToggled(this)"}),
    )
    so = forms.BooleanField(
        label="So",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dayToggled(this)"}),
    )
    ne = forms.BooleanField(
        label="Ne",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dayToggled(this)"}),
    )

    day = MultipleChoiceFieldNoValidation(widget=forms.CheckboxSelectMultiple)

    def _check_date_constraints(self):
        if (
            self.cleaned_data["date_start"] + timedelta(days=14)
            > self.cleaned_data["date_end"]
        ):
            self.add_error(
                "date_end", "Pravidelná událost se musí konat alespoň 2 týdny"
            )

    def _check_training_time_of_chosen_day(self, day):
        from_time_field_name = f"{day}_from"
        to_time_field_name = f"{day}_to"
        from_time = self.cleaned_data[from_time_field_name]
        to_time = self.cleaned_data[to_time_field_name]
        if not (
            from_time.hour < to_time.hour
            or (from_time.hour <= to_time.hour and from_time.minute < to_time.minute)
        ):
            self.add_error(
                to_time_field_name, "Konec tréninku je čas před jeho začátkem"
            )

    def _check_days_chosen_constraints(self):
        days = {d for d in days_shortcut_list() if self.cleaned_data[d]}
        number_of_chosen_days = len(days)
        if number_of_chosen_days in [1, 2, 3]:
            training_dates = [
                parse_czech_date(x).date() for x in self.cleaned_data["day"]
            ]
            weekdays = {x.weekday() for x in training_dates}
            weekdays_shortcut = {weekday_2_day_shortcut(x) for x in weekdays}
            if days != weekdays_shortcut:
                self.add_error(
                    None,
                    "Trénink se musí konat v jednom z určených dnů pro pravidelné opakování",
                )
            for d in days:
                self._check_training_time_of_chosen_day(d)
            d_start = self.cleaned_data["date_start"]
            d_end = self.cleaned_data["date_end"]
            for td in training_dates:
                if not d_start <= td <= d_end:
                    self.add_error(
                        None,
                        "Konkrétní trénink se musí konat v platném rozmezí pravidelné události",
                    )
        else:
            self.add_error(
                None,
                "Není vybrán korektní počet dní týdnu pro pravidelné opakovaní",
            )

    def _check_constraints(self):
        self._check_date_constraints()
        self._check_days_chosen_constraints()

    def clean(self):
        cleaned_data = super().clean()
        self._check_constraints()
        return cleaned_data

    def save(self, commit=True):
        cleaned_data = self.cleaned_data
        instance = super().save(False)

        for name in [
            "name",
            "description",
            "location",
            "capacity",
            "date_start",
            "date_end",
            "category",
        ]:
            setattr(instance, name, cleaned_data[name])

        if commit:
            instance.save()

        children = instance.occurrences_list()
        new_datetimes = []
        for date_raw in self.cleaned_data["day"]:
            datetime_start, datetime_end = self._create_training_datetime(date_raw)
            new_datetimes.append((datetime_start, datetime_end))

        for child in children:
            datetimes = (
                timezone.localtime(child.datetime_start),
                timezone.localtime(child.datetime_end),
            )
            if datetimes in new_datetimes:
                new_datetimes.remove(datetimes)
            elif commit:
                TrainingOccurrence.objects.filter(id=child.id).delete()

        self._save_add_trainings(instance, new_datetimes, commit)
        return instance

    def _save_add_trainings(self, event, new_dates, commit=True):
        for datetime_start, datetime_end in new_dates:
            occurrence = TrainingOccurrence(
                event=event,
                state=EventOrOccurrenceState.OPEN,
                datetime_start=datetime_start,
                datetime_end=datetime_end,
            )
            if commit:
                occurrence.save()

    def _create_training_datetime(self, date_raw):
        date = parse_czech_date(date_raw)
        day_short = weekday_2_day_shortcut(date.weekday())
        time_from = self.cleaned_data[f"{day_short}_from"]
        time_to = self.cleaned_data[f"{day_short}_to"]
        datetime_start = datetime(
            year=date.year,
            month=date.month,
            day=date.day,
            hour=time_from.hour,
            minute=time_from.minute,
            tzinfo=timezone.get_default_timezone(),
        )
        datetime_end = datetime(
            year=date.year,
            month=date.month,
            day=date.day,
            hour=time_to.hour,
            minute=time_to.minute,
            tzinfo=timezone.get_default_timezone(),
        )
        return datetime_start, datetime_end

    def generate_dates(self):
        dates_all = {}
        if (
            hasattr(self, "cleaned_data")
            and "day" in self.cleaned_data
            and "date_start" in self.cleaned_data
            and "date_end" in self.cleaned_data
            and (any(day in self.cleaned_data for day in days_shortcut_list()))
        ):
            start_submitted = self.cleaned_data["date_start"]
            end_submitted = self.cleaned_data["date_end"]
            dates_submitted = [
                parse_czech_date(date_raw).date()
                for date_raw in self.cleaned_data["day"]
            ]
            days_list = [
                d
                for d in [
                    day if day in self.cleaned_data and self.cleaned_data[day] else None
                    for day in days_shortcut_list()
                ]
                if d is not None
            ]
            checked = lambda: start in dates_submitted
        elif self.instance.id is not None:
            event = self.instance
            start_submitted = event.date_start
            end_submitted = event.date_end
            days_list = map(weekday_2_day_shortcut, event.weekdays_occurs_list())
            checked = lambda: event.does_training_take_place_on_date(start)
        else:
            return []
        end = end_submitted
        for day in days_list:
            dates = []
            start = start_submitted
            weekday = day_shortcut_2_weekday(day)

            while start.weekday() != weekday:
                start += timedelta(days=1)

            while start <= end:
                dates.append((start, checked()))
                start += timedelta(days=7)

            dates_all[weekday] = dates
        return dates_all