from datetime import datetime, timedelta
from django.forms import ModelForm, MultipleChoiceField
from django import forms
from .models import Event
from .utils import day_shortcut_2_weekday, weekday_2_day_shortcut
from django.forms import ValidationError
from django.utils import timezone

trainings_per_week_choices = ((1, "1x"), (2, "2x"), (3, "3x"))


class MultipleChoiceFieldNoValidation(MultipleChoiceField):
    def validate(self, value):
        pass


class TrainingForm(ModelForm):
    class Meta:
        model = Event
        fields = ["name", "description", "capacity", "age_limit"]

    starts_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    ends_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    trainings_per_week = forms.ChoiceField(choices=trainings_per_week_choices)

    po = forms.BooleanField(label_suffix="Po", required=False)
    ut = forms.BooleanField(label_suffix="Út", required=False)
    st = forms.BooleanField(label_suffix="St", required=False)
    ct = forms.BooleanField(label_suffix="Čt", required=False)
    pa = forms.BooleanField(label_suffix="Pá", required=False)
    so = forms.BooleanField(label_suffix="So", required=False)
    ne = forms.BooleanField(label_suffix="Ne", required=False)

    from_po = forms.TimeField(required=False)
    to_po = forms.TimeField(required=False)

    from_ut = forms.TimeField(required=False)
    to_ut = forms.TimeField(required=False)

    from_st = forms.TimeField(required=False)
    to_st = forms.TimeField(required=False)

    from_ct = forms.TimeField(required=False)
    to_ct = forms.TimeField(required=False)

    from_pa = forms.TimeField(required=False)
    to_pa = forms.TimeField(required=False)

    from_so = forms.TimeField(required=False)
    to_so = forms.TimeField(required=False)

    from_ne = forms.TimeField(required=False)
    to_ne = forms.TimeField(required=False)

    day = MultipleChoiceFieldNoValidation(widget=forms.CheckboxSelectMultiple)

    def _check_date_constraints(self):
        if (
            self.cleaned_data["starts_date"] + timedelta(days=14)
            > self.cleaned_data["ends_date"]
        ):
            raise ValidationError("Pravidelná událost se koná alespoň 2 týdny")

    def _check_training_time_of_chosen_day(self, day):
        from_time = self.cleaned_data[f"from_{day}"]
        to_time = self.cleaned_data[f"to_{day}"]
        if not (
            from_time.hour < to_time.hour
            or (from_time.hour <= to_time.hour and from_time.minute < to_time.minute)
        ):
            raise ValidationError("Konec tréningu je čas před jeho začátkem")

    def _check_if_training_occurs_on_day_of_week(self, d, weekdays):
        if day_shortcut_2_weekday(d) not in weekdays:
            raise ValidationError(
                "Není vybrán odpovídající počet dní v týdnu vzhledem k počtu tréninků"
            )

    def _check_days_chosen_constraints(self):
        days = ["po", "ut", "st", "ct", "pa", "so", "ne"]
        days = {d for d in days if self.cleaned_data[d]}
        number_of_chosen_days = len(days)
        trainings_per_week = int(self.cleaned_data["trainings_per_week"])
        if trainings_per_week == number_of_chosen_days:
            training_dates = [
                datetime.strptime(x, "%d.%m.%Y").date()
                for x in self.cleaned_data["day"]
            ]
            weekdays = {x.weekday() for x in training_dates}
            weekdays_shortcut = {weekday_2_day_shortcut(x) for x in weekdays}
            if days != weekdays_shortcut:
                raise ValidationError(
                    "Konkrétní trénink se musí konat v jenom z určených dnů pro pravidelné opakování"
                )
            for d in days:
                self._check_training_time_of_chosen_day(d)
                self._check_if_training_occurs_on_day_of_week(d, weekdays)
            d_start = self.cleaned_data["starts_date"]
            d_end = self.cleaned_data["ends_date"]
            for td in training_dates:
                if not d_start <= td <= d_end:
                    raise ValidationError(
                        "Konkrétní trénink se musí konat v platném rozmezí pravidelné události"
                    )
        else:
            raise ValidationError(
                "Není vybrán odpovídající počet dní v týdnu vzhledem k počtu tréninků"
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
        date = datetime.strptime(date_raw, "%d.%m.%Y")
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
