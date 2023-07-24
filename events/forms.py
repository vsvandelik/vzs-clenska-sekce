from datetime import datetime, timedelta, timezone

from django import forms
from django.forms import Form, ModelForm, MultipleChoiceField
from django.utils import timezone
from django_select2.forms import Select2Widget

from persons.models import Person
from vzs.widgets import DateTimePickerWithIcon, DatePickerWithIcon, TimePickerWithIcon
from .models import Event, EventPositionAssignment
from positions.models import EventPosition
from price_lists.models import PriceList
from .utils import (
    weekday_2_day_shortcut,
    parse_czech_date,
    days_shortcut_list,
    day_shortcut_2_weekday,
)


class MultipleChoiceFieldNoValidation(MultipleChoiceField):
    def validate(self, value):
        pass


class EventForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price_list"].queryset = PriceList.templates.all()
        if self.instance.id is not None and self.instance.price_list is not None:
            self.fields["price_list"].queryset = PriceList.nontemplates.filter(
                pk=self.instance.price_list.pk
            )
            self.fields["price_list"].widget.attrs["disabled"] = True
        self.fields["price_list"].required = False


class OneTimeEventForm(EventForm):
    class Meta:
        model = Event
        fields = [
            "name",
            "description",
            "time_start",
            "time_end",
            "capacity",
            "age_limit",
            "price_list",
        ]
        widgets = {
            "time_start": DateTimePickerWithIcon(
                attrs={"onchange": "dateChanged()"},
            ),
            "time_end": DateTimePickerWithIcon(attrs={"onchange": "dateChanged()"}),
            "price_list": Select2Widget(attrs={"onchange": "priceListChanged(this)"}),
        }
        labels = {"price_list": "Ceník"}

    def _check_date_constraints(self):
        if self.cleaned_data["time_start"] >= self.cleaned_data["time_end"]:
            self.add_error(
                "time_end", "Konec události nesmí být dříve než její začátek"
            )

    def clean(self):
        cleaned_data = super().clean()
        self._check_date_constraints()
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        edit = True
        if self.instance.id is None:
            edit = False

        if instance.price_list is not None and instance.price_list.is_template:
            price_list = PriceList.templates.get(pk=instance.price_list.pk)

            price_list_bonuses = []
            for bonus_feature in price_list.bonus_features.all():
                price_list_bonuses.append(
                    bonus_feature.pricelistbonus_set.get(price_list=price_list)
                )

            price_list.pk = None
            price_list.is_template = False
            price_list.save()

            for price_list_bonus in price_list_bonuses:
                price_list_bonus.pk = None
                price_list_bonus.price_list = price_list
                price_list_bonus.save()

            instance.price_list = price_list
        if not edit:
            instance.state = Event.State.FUTURE
        if commit:
            instance.save()
        return instance


class TrainingForm(OneTimeEventForm):
    class Meta:
        model = Event
        fields = ["name", "description", "capacity", "age_limit", "price_list"]
        widgets = {
            "price_list": Select2Widget(attrs={"onchange": "priceListChanged(this)"})
        }
        labels = {"price_list": "Ceník"}

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
                    self.initial[attr] = value.time()

    starts_date = forms.DateField(
        label="Začíná",
        widget=DatePickerWithIcon(attrs={"onchange": "dateChanged()"}),
    )
    ends_date = forms.DateField(
        label="Končí",
        widget=DatePickerWithIcon(attrs={"onchange": "dateChanged()"}),
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
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )
    to_po = forms.TimeField(
        label="Do",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )

    from_ut = forms.TimeField(
        label="Od",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )
    to_ut = forms.TimeField(
        label="Do",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )

    from_st = forms.TimeField(
        label="Od",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )
    to_st = forms.TimeField(
        label="Do",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )

    from_ct = forms.TimeField(
        label="Od",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )
    to_ct = forms.TimeField(
        label="Do",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )

    from_pa = forms.TimeField(
        label="Od",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )
    to_pa = forms.TimeField(
        label="Do",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )

    from_so = forms.TimeField(
        label="Od",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )
    to_so = forms.TimeField(
        label="Do",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )

    from_ne = forms.TimeField(
        label="Od",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
    )
    to_ne = forms.TimeField(
        label="Do",
        required=False,
        widget=TimePickerWithIcon(attrs={"onchange": "timeChanged(this)"}),
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
        cleaned_data = super().clean()
        self._check_constraints()
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
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
        cleaned_data = super().clean()
        pid = cleaned_data["person_id"]
        cleaned_data["event_id"] = self._event_id
        eid = cleaned_data["event_id"]
        try:
            cleaned_data["person"] = Person.objects.get(pk=pid)
            cleaned_data["event"] = Event.objects.get(pk=eid)
            event = cleaned_data["event"]
            event.set_type()
            if not event.is_one_time_event:
                self.add_error("event_id", "Událost {event} není jednorázovou událostí")
            if event.state in [
                Event.State.APPROVED,
                Event.State.FINISHED,
            ]:
                self.add_error(
                    "event_id",
                    f"Událost {event} je uzavřena nebo schválena",
                )
        except Person.DoesNotExist:
            self.add_error("person_id", f"Osoba s id {pid} neexistuje")
        except Event.DoesNotExist:
            self.add_error("event_id", f"Událost s id {eid} neexistuje")
        return cleaned_data


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
        instance = super().save(False)
        if self.instance.id is None:
            instance.event = self.event
        else:
            instance.position = self.position
        if commit:
            instance.save()
