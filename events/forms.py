from datetime import datetime, timedelta
from django.forms import ModelForm, MultipleChoiceField
from django import forms
from .models import Event
from .utils import day_shortcut_2_weekday, weekday_2_day_shortcut, parse_czech_date
from datetime import timezone
from django.utils import timezone

trainings_per_week_choices = ((1, "1x"), (2, "2x"), (3, "3x"))


class MultipleChoiceFieldNoValidation(MultipleChoiceField):
    def validate(self, value):
        pass


class TrainingForm(ModelForm):
    class Meta:
        model = Event
        fields = ["name", "description", "capacity", "age_limit"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        event = kwargs["instance"]
        if event is not None:
            self.initial["starts_date"] = timezone.localtime(event.time_start).date()
            self.initial["ends_date"] = timezone.localtime(event.time_end).date()
            event.extend_2_top_training()
            for weekday in event.weekdays:
                day_shortcut = weekday_2_day_shortcut(weekday)
                self.initial[day_shortcut] = True
            self.initial["trainings_per_week"] = len(event.weekdays)
            for attr, value in event.__dict__.items():
                if attr[:5] == "from_" or attr[:3] == "to_":
                    self.initial[attr] = value

    starts_date = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date", "onchange": "dateChanged()"}, format="%Y-%m-%d"
        )
    )
    ends_date = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date", "onchange": "dateChanged()"}, format="%Y-%m-%d"
        )
    )
    trainings_per_week = forms.ChoiceField(
        choices=trainings_per_week_choices,
        widget=forms.Select(attrs={"onchange": "trainingsPerWeekChanged()"}),
    )

    po = forms.BooleanField(
        label_suffix="Po",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dowToggled(this)"}),
    )
    ut = forms.BooleanField(
        label_suffix="Út",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dowToggled(this)"}),
    )
    st = forms.BooleanField(
        label_suffix="St",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dowToggled(this)"}),
    )
    ct = forms.BooleanField(
        label_suffix="Čt",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dowToggled(this)"}),
    )
    pa = forms.BooleanField(
        label_suffix="Pá",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dowToggled(this)"}),
    )
    so = forms.BooleanField(
        label_suffix="So",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dowToggled(this)"}),
    )
    ne = forms.BooleanField(
        label_suffix="Ne",
        required=False,
        widget=forms.CheckboxInput(attrs={"onchange": "dowToggled(this)"}),
    )

    from_po = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )
    to_po = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )

    from_ut = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )
    to_ut = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )

    from_st = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )
    to_st = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )

    from_ct = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )
    to_ct = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )

    from_pa = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )
    to_pa = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )

    from_so = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )
    to_so = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )

    from_ne = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )
    to_ne = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "validateTimes(this)"}, format="%H:%M"
        ),
    )

    day = MultipleChoiceFieldNoValidation(widget=forms.CheckboxSelectMultiple)

    def _check_date_constraints(self):
        if (
            self.cleaned_data["starts_date"] + timedelta(days=14)
            > self.cleaned_data["ends_date"]
        ):
            self.add_error("ends_date", "Pravidelná událost se koná alespoň 2 týdny")

    def _check_training_time_of_chosen_day(self, day):
        from_time_field_name = f"from_{day}"
        to_time_field_name = f"to_{day}"
        from_time = self.cleaned_data[from_time_field_name]
        to_time = self.cleaned_data[to_time_field_name]
        if not (
            from_time.hour < to_time.hour
            or (from_time.hour <= to_time.hour and from_time.minute < to_time.minute)
        ):
            self.add_error(
                to_time_field_name, "Konec tréningu je čas před jeho začátkem"
            )

    def _check_if_training_occurs_on_dow(self, d, weekdays):
        if day_shortcut_2_weekday(d) not in weekdays:
            self.add_error(
                None,
                "Není vybrán odpovídající počet dní v týdnu vzhledem k počtu tréninků",
            )

    def _check_days_chosen_constraints(self):
        days = ["po", "ut", "st", "ct", "pa", "so", "ne"]
        days = {d for d in days if self.cleaned_data[d]}
        number_of_chosen_days = len(days)
        trainings_per_week = int(self.cleaned_data["trainings_per_week"])
        if trainings_per_week == number_of_chosen_days:
            training_dates = [
                parse_czech_date(x).date() for x in self.cleaned_data["day"]
            ]
            weekdays = {x.weekday() for x in training_dates}
            weekdays_shortcut = {weekday_2_day_shortcut(x) for x in weekdays}
            if days != weekdays_shortcut:
                self.add_error(
                    None,
                    "Konkrétní trénink se musí konat v jednom z určených dnů pro pravidelné opakování",
                )
            for d in days:
                self._check_training_time_of_chosen_day(d)
                self._check_if_training_occurs_on_dow(d, weekdays)
            d_start = self.cleaned_data["starts_date"]
            d_end = self.cleaned_data["ends_date"]
            for td in training_dates:
                if not d_start <= td <= d_end:
                    self.add_error(
                        None,
                        "Konkrétní trénink se musí konat v platném rozmezí pravidelné události",
                    )
        else:
            self.add_error(
                None,
                "Není vybrán odpovídající počet dní v týdnu vzhledem k počtu tréninků",
            )

    def _check_constraints(self):
        self._check_date_constraints()
        self._check_days_chosen_constraints()

    def clean(self):
        super().clean()
        self._check_constraints()

    def save(self, commit=True):
        instance = self.instance
        if self.instance.id is None:
            instance = Event.objects.create()
            instance.name = self.cleaned_data["name"]
            instance.description = self.cleaned_data["description"]
            instance.capacity = self.cleaned_data["capacity"]
            instance.age_limit = self.cleaned_data["age_limit"]
            instance.state = Event.State.FUTURE
            instance.time_start = self.cleaned_data["starts_date"]
            instance.time_end = self.cleaned_data["ends_date"]
        if commit:
            instance.save()
        children = instance.get_children_trainings_sorted()
        new_dates = []
        for date_raw in self.cleaned_data["day"]:
            date_start, date_end = self._create_training_date(date_raw)
            new_dates.append((date_start, date_end))

        for child in children:
            times = (
                timezone.localtime(child.time_start),
                timezone.localtime(child.time_end),
            )
            if times in new_dates:
                new_dates.remove(times)
            elif commit:
                Event.objects.filter(id=child.id).delete()

        parent_id = instance.id
        instance._state.adding = True
        self._save_add_trainings(instance, parent_id, new_dates, commit)
        return instance

    def _save_add_trainings(self, instance, parent_id, new_dates, commit=True):
        for date_start, date_end in new_dates:
            instance.pk = None
            instance.parent_id = parent_id
            instance.time_start = date_start
            instance.time_end = date_end
            if commit:
                instance.save()

    def _create_training_date(self, date_raw):
        date = parse_czech_date(date_raw)
        day_short = weekday_2_day_shortcut(date.weekday())
        time_from = self.cleaned_data[f"from_{day_short}"]
        time_to = self.cleaned_data[f"to_{day_short}"]
        date_start = datetime(
            year=date.year,
            month=date.month,
            day=date.day,
            hour=time_from.hour,
            minute=time_from.minute,
            tzinfo=timezone.get_default_timezone(),
        )
        date_end = datetime(
            year=date.year,
            month=date.month,
            day=date.day,
            hour=time_to.hour,
            minute=time_to.minute,
            tzinfo=timezone.get_default_timezone(),
        )
        return date_start, date_end
