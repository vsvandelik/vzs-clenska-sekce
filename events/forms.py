from datetime import datetime, timedelta
from django.forms import Form, ModelForm, MultipleChoiceField
from django import forms
from .models import Event, EventPosition, EventPositionAssignment
from .utils import (
    weekday_2_day_shortcut,
    parse_czech_date,
    days_shortcut_list,
    day_shortcut_2_weekday,
)
from datetime import timezone
from django.utils import timezone
from persons.models import Person, Feature
from django_select2.forms import Select2Widget
from django.forms.widgets import CheckboxInput
from django.core.validators import MaxValueValidator, MinValueValidator


class MultipleChoiceFieldNoValidation(MultipleChoiceField):
    def validate(self, value):
        pass


class OneTimeEventForm(ModelForm):
    class Meta:
        model = Event
        fields = [
            "name",
            "description",
            "time_start",
            "time_end",
            "capacity",
            "age_limit",
        ]
        widgets = {
            "time_start": forms.DateTimeInput(
                attrs={"type": "datetime-local", "onchange": "dateChanged()"},
                format="%Y-%m-%dT%H:%M:%S",
            ),
            "time_end": forms.DateTimeInput(
                attrs={"type": "datetime-local", "onchange": "dateChanged()"},
                format="%Y-%m-%dT%H:%M:%S",
            ),
        }

    def _check_date_constraints(self):
        if self.cleaned_data["time_start"] >= self.cleaned_data["time_end"]:
            self.add_error(
                "time_end", "Konec události nesmí být dříve než její začátek"
            )

    def clean(self):
        super().clean()
        self._check_date_constraints()

    def save(self, commit=True):
        instance = self.instance
        edit = True
        if self.instance.id is None:
            edit = False
        super().save(commit)
        if not edit:
            instance.state = Event.State.FUTURE
            instance.save()
        return instance


class TrainingForm(OneTimeEventForm):
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
            for attr, value in event.__dict__.items():
                if attr[:5] == "from_" or attr[:3] == "to_":
                    self.initial[attr] = value

    starts_date = forms.DateField(
        label="Začíná",
        widget=forms.DateInput(
            attrs={"type": "date", "onchange": "dateChanged()"}, format="%Y-%m-%d"
        ),
    )
    ends_date = forms.DateField(
        label="Končí",
        widget=forms.DateInput(
            attrs={"type": "date", "onchange": "dateChanged()"}, format="%Y-%m-%d"
        ),
    )
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

    from_po = forms.TimeField(
        label="Od",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )
    to_po = forms.TimeField(
        label="Do",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )

    from_ut = forms.TimeField(
        label="Od",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )
    to_ut = forms.TimeField(
        label="Do",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )

    from_st = forms.TimeField(
        label="Od",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )
    to_st = forms.TimeField(
        label="Do",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )

    from_ct = forms.TimeField(
        label="Od",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )
    to_ct = forms.TimeField(
        label="Do",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )

    from_pa = forms.TimeField(
        label="Od",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )
    to_pa = forms.TimeField(
        label="Do",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )

    from_so = forms.TimeField(
        label="Od",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )
    to_so = forms.TimeField(
        label="Do",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )

    from_ne = forms.TimeField(
        label="Od",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )
    to_ne = forms.TimeField(
        label="Do",
        required=False,
        widget=forms.TimeInput(
            attrs={"type": "time", "onchange": "timeChanged(this)"}, format="%H:%M"
        ),
    )

    day = MultipleChoiceFieldNoValidation(widget=forms.CheckboxSelectMultiple)

    def _check_date_constraints(self):
        if (
            self.cleaned_data["starts_date"] + timedelta(days=14)
            > self.cleaned_data["ends_date"]
        ):
            self.add_error(
                "ends_date", "Pravidelná událost se musí konat alespoň 2 týdny"
            )

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
                to_time_field_name, "Konec tréninku je čas před jeho začátkem"
            )

    def _check_days_chosen_constraints(self):
        days = ["po", "ut", "st", "ct", "pa", "so", "ne"]
        days = {d for d in days if self.cleaned_data[d]}
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
                "Není vybrán korektní počet dní týdnu pro pravidelné opakovaní",
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
            instance.state = Event.State.FUTURE
        instance.name = self.cleaned_data["name"]
        instance.description = self.cleaned_data["description"]
        instance.capacity = self.cleaned_data["capacity"]
        instance.age_limit = self.cleaned_data["age_limit"]
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

    def generate_dates(self):
        dates_all = {}
        if (
            hasattr(self, "cleaned_data")
            and "day" in self.cleaned_data
            and "starts_date" in self.cleaned_data
            and "ends_date" in self.cleaned_data
            and (any(day in self.cleaned_data for day in days_shortcut_list()))
        ):
            start_submitted = self.cleaned_data["starts_date"]
            end_submitted = self.cleaned_data["ends_date"]
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
        elif self.instance.id:
            event = self.instance
            start_submitted = event.time_start.date()
            end_submitted = event.time_end.date()
            days_list = map(weekday_2_day_shortcut, event.weekdays)
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


class AddDeleteParticipantFromOneTimeEventForm(Form):
    person_id = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        self._event_id = kwargs.pop("event_id")
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        pid = self.cleaned_data["person_id"]
        self.cleaned_data["event_id"] = self._event_id
        eid = self.cleaned_data["event_id"]
        try:
            self.cleaned_data["person"] = Person.objects.get(pk=pid)
            self.cleaned_data["event"] = Event.objects.get(pk=eid)
            self.cleaned_data["event"].set_type()
            if not self.cleaned_data["event"].is_one_time_event:
                self.add_error("event_id", "Událost {event} není jednorázovou událostí")
            if self.cleaned_data["event"].state in [
                Event.State.APPROVED,
                Event.State.FINISHED,
            ]:
                self.add_error(
                    "event_id",
                    f"Událost {self.cleaned_data['event']} je uzavřena nebo schválena",
                )
        except Person.DoesNotExist:
            self.add_error("person_id", f"Osoba s id {pid} neexistuje")
        except Event.DoesNotExist:
            self.add_error("event_id", f"Událost s id {eid} neexistuje")


class AddFeatureRequirementToPositionForm(Form):
    feature_id = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        self._position_id = kwargs.pop("position_id")
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        self.cleaned_data["position_id"] = self._position_id
        pid = self.cleaned_data["position_id"]
        fid = self.cleaned_data["feature_id"]
        try:
            self.cleaned_data["feature"] = Feature.objects.get(pk=fid)
            self.cleaned_data["position"] = EventPosition.objects.get(pk=pid)
        except EventPosition.DoesNotExist:
            self.add_error("position_id", f"Pozice s id {pid} neexistuje")
        except Feature.DoesNotExist:
            self.add_error(
                "feature_id",
                f"Kvalifikace, oprávnění ani vybavení s id {fid} neexistuje",
            )
        return self.cleaned_data


class EventPositionAssignmentForm(ModelForm):
    class Meta:
        model = EventPositionAssignment
        fields = [
            "position",
            "count",
        ]
        labels = {"position": "Pozice"}
        widgets = {
            "position": Select2Widget(attrs={"onchange": "positionChanged(this)"})
        }

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event")
        self.position = kwargs.pop("position", None)
        super().__init__(*args, **kwargs)
        self.fields["count"].widget.attrs["min"] = 1
        if self.position is not None:
            self.fields["position"].widget.attrs["disabled"] = True
        else:
            self.fields["position"].queryset = EventPosition.objects.filter(
                pk__in=EventPosition.objects.all()
                .values_list("pk", flat=True)
                .difference(
                    EventPositionAssignment.objects.filter(
                        event=self.event
                    ).values_list("position_id", flat=True)
                )
            )

    def save(self, commit=True):
        instance = self.instance
        if self.instance.id is None:
            instance.event = self.event
        else:
            instance.position = self.position
        instance.save()


class AgeLimitPositionForm(ModelForm):
    class Meta:
        model = EventPosition
        fields = ["min_age_enabled", "max_age_enabled", "min_age", "max_age"]
        labels = {
            "min_age_enabled": "Aktivní",
            "max_age_enabled": "Aktivní",
            "min_age": "Min",
            "max_age": "Max",
        }
        widgets = {
            "min_age_enabled": CheckboxInput(
                attrs={"onchange": "minAgeCheckboxClicked(this)"}
            ),
            "max_age_enabled": CheckboxInput(
                attrs={"onchange": "maxAgeCheckboxClicked(this)"}
            ),
        }

    def clean(self):
        super().clean()
        if not self.cleaned_data["min_age_enabled"]:
            self.cleaned_data["min_age"] = self.instance.min_age
        if not self.cleaned_data["max_age_enabled"]:
            self.cleaned_data["max_age"] = self.instance.max_age

        fields = ["min_age", "max_age"]
        for f in fields:
            if self.cleaned_data[f"{f}_enabled"]:
                if f not in self.cleaned_data or self.cleaned_data[f] is None:
                    self.add_error(f, "Toto pole je nutné vyplnit")

        if (
            len(self.cleaned_data) == 4
            and self.cleaned_data["min_age_enabled"]
            and self.cleaned_data["max_age_enabled"]
            and self.cleaned_data["min_age"] is not None
            and self.cleaned_data["max_age"] is not None
        ):
            if self.cleaned_data["min_age"] > self.cleaned_data["max_age"]:
                self.add_error(
                    "max_age",
                    "Hodnota minimální věkové hranice musí být menší nebo rovna hodnotě maximální věkové hranice",
                )
        return self.cleaned_data
