from datetime import datetime, timedelta, timezone

from django import forms
from django.db.models import Q
from django.forms import ModelForm
from django.utils import timezone

from events.forms import MultipleChoiceFieldNoValidation
from events.forms_bases import (
    EventForm,
    ParticipantEnrollmentForm,
    EnrollMyselfParticipantForm,
    BulkApproveParticipantsForm,
    EventFormMixin,
    OrganizerAssignmentForm,
    EnrollMyselfOrganizerOccurrenceForm,
    UnenrollMyselfOccurrenceForm,
    OccurrenceFormMixin,
    PersonMetaMixin,
    ActivePersonFormMixin,
    ReopenOccurrenceMixin,
)
from events.models import (
    EventOrOccurrenceState,
    ParticipantEnrollment,
)
from events.utils import parse_czech_date
from persons.models import Person, PersonHourlyRate
from trainings.utils import (
    weekday_2_day_shortcut,
    days_shortcut_list,
    day_shortcut_2_weekday,
)
from transactions.models import Transaction
from vzs.forms import WithoutFormTagFormHelper
from vzs.widgets import TimePickerWithIcon
from .models import (
    Training,
    TrainingOccurrence,
    TrainingReplaceabilityForParticipants,
    TrainingParticipantEnrollment,
    TrainingWeekdays,
    CoachPositionAssignment,
    CoachOccurrenceAssignment,
    TrainingParticipantAttendance,
    TrainingAttendance,
)


class CoachAssignmentUpdateAttendanceProvider:
    def coach_assignment_update_attendance(self, instance, event, occurrences=None):
        if occurrences is None:
            occurrences = event.eventoccurrence_set.filter(
                state=EventOrOccurrenceState.OPEN
            )

        for occurrence in occurrences:
            (
                organizer_assignment,
                _,
            ) = CoachOccurrenceAssignment.objects.update_or_create(
                occurrence=occurrence,
                person=instance.person,
                defaults={
                    "position_assignment": instance.position_assignment,
                    "person": instance.person,
                    "occurrence": occurrence,
                    "state": TrainingAttendance.PRESENT,
                },
            )
            organizer_assignment.position_assignment = instance.position_assignment
            organizer_assignment.save()


class TrainingParticipantEnrollmentUpdateAttendanceProvider:
    def participant_enrollment_update_attendance(self, instance, occurrences_list=None):
        if occurrences_list is None:
            occurrences_list = instance.event.eventoccurrence_set.filter(
                state=EventOrOccurrenceState.OPEN
            )

        for occurrence in occurrences_list:
            if (
                instance.state == ParticipantEnrollment.State.APPROVED
                and instance.attends_on_weekday(occurrence.weekday())
            ):
                TrainingParticipantAttendance.objects.update_or_create(
                    occurrence=occurrence,
                    person=instance.person,
                    defaults={
                        "enrollment": instance,
                        "person": instance.person,
                        "occurrence": occurrence,
                        "state": TrainingAttendance.PRESENT,
                    },
                )

            else:
                attendance = TrainingParticipantAttendance.objects.filter(
                    occurrence=occurrence, person=instance.person
                ).first()
                if attendance is not None:
                    attendance.delete()


class TrainingForm(
    CoachAssignmentUpdateAttendanceProvider,
    TrainingParticipantEnrollmentUpdateAttendanceProvider,
    EventForm,
):
    class Meta(EventForm.Meta):
        model = Training
        fields = [
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
        ] + EventForm.Meta.fields
        widgets = {
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
        } | EventForm.Meta.widgets

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

        self.helper = WithoutFormTagFormHelper()

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
            self.cleaned_data["weekdays"] = {x.weekday() for x in training_dates}
            weekdays_shortcut = {
                weekday_2_day_shortcut(x) for x in self.cleaned_data["weekdays"]
            }
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
        self.cleaned_data = super().clean()
        self._check_constraints()
        return self.cleaned_data

    def save(self, commit=True):
        instance = super().save(False)

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
        weekdays = self.cleaned_data["weekdays"]
        if commit:
            for (
                participant_enrollment
            ) in instance.trainingparticipantenrollment_set.all():
                for weekday_attending_obj in participant_enrollment.weekdays.all():
                    if weekday_attending_obj.weekday not in weekdays:
                        weekday_attending_obj.delete()

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
                for coach_assignment in event.coachpositionassignment_set.all():
                    super().coach_assignment_update_attendance(
                        coach_assignment, event, [occurrence]
                    )
                for (
                    participant_enrollment
                ) in event.trainingparticipantenrollment_set.all():
                    super().participant_enrollment_update_attendance(
                        participant_enrollment, [occurrence]
                    )

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


class TrainingReplaceableForm(forms.ModelForm):
    class Meta:
        model = TrainingReplaceabilityForParticipants
        fields = ["training_2"]

    def __init__(self, *args, training_1, **kwargs):
        super().__init__(*args, **kwargs)
        self.training_1 = training_1

    def clean_training_2(self):
        training_2 = self.cleaned_data.get("training_2")

        if (
            self.training_1
            and training_2
            and self.training_1.category != training_2.category
        ):
            raise forms.ValidationError("Tréninky musí být stejné kategorie")

        return training_2

    def clean(self):
        cleaned_data = super().clean()
        training_1 = self.training_1
        training_2 = cleaned_data.get("training_2")

        if TrainingReplaceabilityForParticipants.objects.filter(
            Q(training_1=training_1, training_2=training_2)
        ).exists():
            self.add_error(
                None,
                "Tato kombinace tréninků již existuje",
            )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)

        training_1 = self.training_1
        training_2 = self.cleaned_data.get("training_2")

        if commit:
            instance.training_1 = training_1
            instance.save()

        if not TrainingReplaceabilityForParticipants.objects.filter(
            Q(training_2=training_1, training_1=training_2)
        ).exists():
            TrainingReplaceabilityForParticipants.objects.create(
                training_1=training_2,
                training_2=training_1,
            )

        return instance


class TrainingWeekdaysSelectionMixin:
    def clean_parse_weekdays(self):
        if (
            "weekdays" not in self.cleaned_data
            or len(self.cleaned_data["weekdays"]) == 0
        ):
            self.add_error(None, "Nejsou vybrány žádné dny v týdnu")

        weekdays_list = self.event.weekdays_list()
        for i in range(len(self.cleaned_data["weekdays"])):
            weekday_str = self.cleaned_data["weekdays"][i]
            try:
                weekday = int(weekday_str)
                if weekday not in weekdays_list:
                    self.add_error(None, "Tento den v týdnu se trénink neodehrává")
                self.cleaned_data["weekdays"][i] = weekday
            except ValueError:
                self.add_error(None, "Neplatná hodnota dne v týdnu")

    def checked_weekdays(self):
        if hasattr(self, "cleaned_data") and "weekdays" in self.cleaned_data:
            return self.cleaned_data["weekdays"]
        elif (
            self.instance.id is not None
            and self.instance.state != ParticipantEnrollment.State.REJECTED
        ):
            return [weekday_obj.weekday for weekday_obj in self.instance.weekdays.all()]

        return self.event.free_weekdays_list()


class InitializeWeekdaysProvider:
    def initialize_weekdays(self, enrollment, weekdays_cleaned):
        for weekday in weekdays_cleaned:
            weekday_obj = TrainingWeekdays.get_or_create(weekday)
            enrollment.weekdays.add(weekday_obj)


class TrainingParticipantEnrollmentForm(
    TrainingWeekdaysSelectionMixin,
    ParticipantEnrollmentForm,
    InitializeWeekdaysProvider,
    TrainingParticipantEnrollmentUpdateAttendanceProvider,
):
    class Meta(ParticipantEnrollmentForm.Meta):
        model = TrainingParticipantEnrollment

    weekdays = MultipleChoiceFieldNoValidation(widget=forms.CheckboxSelectMultiple)

    def clean(self):
        self.cleaned_data = super().clean()
        if self.cleaned_data["state"] != ParticipantEnrollment.State.REJECTED:
            super().clean_parse_weekdays()
        else:
            self.cleaned_data["weekdays"] = []
        return self.cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        weekdays_cleaned = self.cleaned_data["weekdays"]
        if instance.id is not None or commit:
            if instance.id is None:
                instance.save()
            instance_weekdays_objs = instance.weekdays.all()
            for weekday_obj in instance_weekdays_objs:
                if weekday_obj.weekday not in weekdays_cleaned:
                    weekday_obj.delete()
                else:
                    weekdays_cleaned.remove(weekday_obj.weekday)

        if commit:
            super().initialize_weekdays(instance, weekdays_cleaned)
            instance.save()
            super().participant_enrollment_update_attendance(instance)
        return instance


class TrainingEnrollMyselfParticipantForm(
    TrainingWeekdaysSelectionMixin,
    EnrollMyselfParticipantForm,
    InitializeWeekdaysProvider,
    TrainingParticipantEnrollmentUpdateAttendanceProvider,
):
    class Meta(EnrollMyselfParticipantForm.Meta):
        model = TrainingParticipantEnrollment

    weekdays = MultipleChoiceFieldNoValidation(widget=forms.CheckboxSelectMultiple)

    def clean(self):
        self.cleaned_data = super().clean()
        super().clean_parse_weekdays()
        return self.cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        instance.training = self.event
        instance.state = ParticipantEnrollment.State.SUBSTITUTE
        weekdays = self.cleaned_data["weekdays"]
        if (
            self.event.participants_enroll_state == ParticipantEnrollment.State.APPROVED
            and self.event.can_person_enroll_as_participant(self.person)
            and all(map(instance.training.has_weekday_free_spot, weekdays))
        ):
            instance.state = ParticipantEnrollment.State.APPROVED

        if commit:
            instance.save()
            super().initialize_weekdays(instance, weekdays)
            instance.save()
            super().participant_enrollment_update_attendance(instance)
        return instance


class CoachAssignmentForm(
    EventFormMixin, CoachAssignmentUpdateAttendanceProvider, OrganizerAssignmentForm
):
    class Meta(OrganizerAssignmentForm.Meta):
        model = CoachPositionAssignment

    main_coach_assignment = forms.BooleanField(
        label="Garantující trenér",
        required=False,
        widget=forms.CheckboxInput(),
    )

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop("person", None)
        super().__init__(*args, **kwargs)

        if self.instance.id is not None:
            if self.event.main_coach_assignment is not None:
                self.fields["main_coach_assignment"].initial = (
                    self.event.main_coach_assignment.person == self.person
                )

            self.fields["person"].widget.attrs["disabled"] = True
        else:
            self.fields["person"].queryset = Person.objects.filter(
                ~Q(coachpositionassignment__training=self.event)
            )
        self.fields[
            "position_assignment"
        ].queryset = self.event.eventpositionassignment_set.all()

        self.helper = WithoutFormTagFormHelper()

    def save(self, commit=True):
        instance = super().save(False)
        instance.training = self.event
        if instance.id is not None:
            instance.person = self.person

        if self.cleaned_data["main_coach_assignment"]:
            self.event.main_coach_assignment = instance
        elif (
            self.event.main_coach_assignment is not None
            and instance.person == self.event.main_coach_assignment.person
        ):
            self.event.main_coach_assignment = None

        if commit:
            super().coach_assignment_update_attendance(instance, self.event)
            instance.save()
            self.event.save()
        return instance


class CoachAssignmentDeleteForm(ModelForm):
    class Meta:
        model = CoachPositionAssignment
        fields = []

    def save(self, commit=True):
        instance = super().save(False)
        if commit:
            CoachOccurrenceAssignment.objects.filter(
                person=instance.person, occurrence__event=instance.training
            ).delete()
            instance.delete()
        return instance


class TrainingBulkApproveParticipantsForm(
    TrainingParticipantEnrollmentUpdateAttendanceProvider, BulkApproveParticipantsForm
):
    class Meta(BulkApproveParticipantsForm.Meta):
        model = Training

    def save(self, commit=True):
        instance = super().save(False)
        enrollments_2_approve = instance.substitute_enrollments_2_capacity()

        for enrollment in enrollments_2_approve:
            enrollment.state = ParticipantEnrollment.State.APPROVED
            if commit:
                enrollment.save()
                super().participant_enrollment_update_attendance(enrollment)

        self.cleaned_data["count"] = len(enrollments_2_approve)
        return instance


class CancelExcuseForm(ModelForm):
    class Meta:
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.state != TrainingAttendance.EXCUSED:
            self.add_error(None, f"Osoba {self.instance.person} není omluvena")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        instance.state = TrainingAttendance.PRESENT
        if commit:
            instance.save()
        return instance


class CancelCoachExcuseForm(CancelExcuseForm):
    class Meta(CancelExcuseForm.Meta):
        model = CoachOccurrenceAssignment


class ExcuseFormMixin:
    def save(self, commit=True):
        instance = super().save(False)
        instance.state = TrainingAttendance.EXCUSED
        if commit:
            instance.save()
        return instance


class ExcuseCoachForm(ExcuseFormMixin, ModelForm):
    class Meta:
        model = CoachOccurrenceAssignment
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.occurrence.event.coaches.contains(self.instance.person):
            self.add_error(None, "Omluvit neúčast je možné pouze u řádného trenéra")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        instance.state = TrainingAttendance.EXCUSED
        if commit:
            instance.save()
        return instance


class ExcuseMyselfCoachForm(ExcuseCoachForm):
    class Meta(ExcuseCoachForm.Meta):
        pass

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.occurrence.can_coach_excuse(self.instance.person):
            self.add_error(None, "Již se není možné odhlásit z trenérské pozice")
        return cleaned_data


class CoachExcuseForm(ExcuseCoachForm):
    class Meta(ExcuseCoachForm.Meta):
        pass


class TrainingEnrollMyselfOrganizerOccurrenceForm(EnrollMyselfOrganizerOccurrenceForm):
    class Meta(EnrollMyselfOrganizerOccurrenceForm.Meta):
        model = CoachOccurrenceAssignment

    def save(self, commit=True):
        instance = super().save(False)
        instance.state = TrainingAttendance.PRESENT
        if commit:
            instance.save()
        return instance


class TrainingUnenrollMyselfOrganizerFromOccurrenceForm(UnenrollMyselfOccurrenceForm):
    class Meta(UnenrollMyselfOccurrenceForm.Meta):
        model = CoachOccurrenceAssignment


class CoachOccurrenceAssignmentForm(OccurrenceFormMixin, OrganizerAssignmentForm):
    class Meta(OrganizerAssignmentForm.Meta):
        model = CoachOccurrenceAssignment

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop("person", None)
        super().__init__(*args, **kwargs)

        if self.instance.id is not None:
            self.fields["person"].widget.attrs["disabled"] = True
        else:
            self.fields["person"].queryset = Person.objects.filter(
                ~Q(coachoccurrenceassignment__occurrence=self.occurrence)
            )
        self.fields[
            "position_assignment"
        ].queryset = self.occurrence.event.eventpositionassignment_set.all()

    def save(self, commit=True):
        instance = super().save(False)
        instance.occurrence = self.occurrence
        instance.state = TrainingAttendance.PRESENT
        if instance.id is not None:
            instance.person = self.person
        if commit:
            instance.save()
        return instance


class ExcuseParticipantForm(ExcuseFormMixin, ModelForm):
    class Meta:
        model = TrainingParticipantAttendance
        fields = []

    def clean(self):
        cleaned_data = super().clean()

        if not self.instance.occurrence.event.enrolled_participants.contains(
            self.instance.person
        ):
            self.add_error(None, "Omluvit neúčast je možné pouze u řádného účastníka")

        return cleaned_data


class ParticipantExcuseForm(ExcuseParticipantForm):
    class Meta(ExcuseParticipantForm.Meta):
        pass


class CancelParticipantExcuseForm(CancelExcuseForm):
    class Meta(CancelExcuseForm.Meta):
        model = TrainingParticipantAttendance


class ExcuseMyselfParticipantForm(ExcuseParticipantForm):
    class Meta(ExcuseParticipantForm.Meta):
        pass

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.occurrence.can_participant_excuse(self.instance.person):
            self.add_error(None, "Již se není možné odhlásit jako účastník")
        return cleaned_data


class TrainingUnenrollMyselfParticipantFromOccurrenceForm(UnenrollMyselfOccurrenceForm):
    class Meta(UnenrollMyselfOccurrenceForm.Meta):
        model = TrainingParticipantAttendance


class TrainingParticipantAttendanceForm(OccurrenceFormMixin, ModelForm):
    class Meta(PersonMetaMixin):
        model = TrainingParticipantAttendance

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop("person", None)
        super().__init__(*args, **kwargs)
        if self.instance.id is not None:
            self.fields["person"].widget.attrs["disabled"] = True
        else:
            self.fields["person"].queryset = Person.objects.filter(
                ~Q(trainingparticipantattendance__occurrence=self.occurrence)
            )

    def save(self, commit=True):
        instance = super().save(False)
        instance.occurrence = self.occurrence
        instance.state = TrainingAttendance.PRESENT
        if instance.id is not None:
            instance.person = self.person
        if commit:
            instance.save()
        return instance


class TrainingEnrollMyselfParticipantOccurrenceForm(
    OccurrenceFormMixin, ActivePersonFormMixin, ModelForm
):
    class Meta:
        model = TrainingParticipantAttendance
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        if not self.occurrence.can_participant_enroll(self.person):
            self.add_error(
                None, "Nemáte oprávnění k jednorázovému přihlášení na tento trénink"
            )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        instance.person = self.person
        instance.occurrence = self.occurrence
        instance.state = TrainingAttendance.PRESENT
        if commit:
            instance.save()
        return instance


class TrainingFillAttendanceForm(ModelForm):
    class Meta:
        model = TrainingOccurrence
        fields = []

    def __init__(self, *args, **kwargs):
        post = kwargs.pop("request").POST
        self.coaches = post.getlist("coaches")
        self.participants = post.getlist("participants")
        super().__init__(*args, **kwargs)

    def _clean_parse_coaches(self):
        coach_assignments = []
        for coach_assignment_id_str in self.coaches:
            try:
                coach_assignment_id = int(coach_assignment_id_str)
            except ValueError:
                self.add_error(None, "Neplatná hodnota přiřazení trenéra")
                continue
            coach_assignment = CoachOccurrenceAssignment.objects.filter(
                id=coach_assignment_id
            ).first()
            if (
                coach_assignment is None
                or coach_assignment.state == TrainingAttendance.EXCUSED
            ):
                self.add_error(None, "Neplatná hodnota přiřazení trenéra")
                continue
            coach_assignments.append(coach_assignment)
        self.cleaned_data["coaches"] = coach_assignments

    def _clean_parse_participants(self):
        participant_assignments = []
        for participant_assignment_id_str in self.participants:
            try:
                participant_assignment_id = int(participant_assignment_id_str)
            except ValueError:
                self.add_error(None, "Neplatná hodnota přiřazení účastníka")
                continue
            participant_assignment = TrainingParticipantAttendance.objects.filter(
                id=participant_assignment_id
            ).first()
            if (
                participant_assignment is None
                or participant_assignment.state == TrainingAttendance.EXCUSED
            ):
                self.add_error(None, "Neplatná hodnota přiřazení účastníka")
                continue
            participant_assignments.append(participant_assignment)
        self.cleaned_data["participants"] = participant_assignments

    def checked_participant_assignments(self):
        if hasattr(self, "cleaned_data") and "participants" in self.cleaned_data:
            return self.cleaned_data["participants"]
        if self.instance.is_opened:
            return TrainingParticipantAttendance.objects.filter(
                Q(occurrence=self.instance) & ~Q(state=TrainingAttendance.EXCUSED)
            )
        return TrainingParticipantAttendance.objects.filter(
            occurrence=self.instance, state=TrainingAttendance.PRESENT
        )

    def checked_coach_assignments(self):
        if hasattr(self, "cleaned_data") and "coaches" in self.cleaned_data:
            return self.cleaned_data["coaches"]
        if self.instance.is_opened:
            return CoachOccurrenceAssignment.objects.filter(
                Q(occurrence=self.instance) & ~Q(state=TrainingAttendance.EXCUSED)
            )
        return CoachOccurrenceAssignment.objects.filter(
            occurrence=self.instance, state=TrainingAttendance.PRESENT
        )

    def clean(self):
        cleaned_data = super().clean()
        self._clean_parse_coaches()
        self._clean_parse_participants()
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        instance.state = EventOrOccurrenceState.CLOSED

        observed_assignments = [
            TrainingParticipantAttendance.objects.filter(
                ~Q(state=TrainingAttendance.EXCUSED) & Q(occurrence=instance)
            ),
            CoachOccurrenceAssignment.objects.filter(
                ~Q(state=TrainingAttendance.EXCUSED) & Q(occurrence=instance)
            ),
        ]

        assignments = [self.cleaned_data["participants"], self.cleaned_data["coaches"]]

        for i in range(0, 2):
            entity_assignments = observed_assignments[i]
            for entity_assignment in entity_assignments:
                if entity_assignment in assignments[i]:
                    entity_assignment.state = TrainingAttendance.PRESENT
                    if type(entity_assignment) is CoachOccurrenceAssignment:
                        occurrence_date = instance.datetime_start.date()
                        person_rate = PersonHourlyRate.get_person_hourly_rates(
                            entity_assignment.person
                        )
                        if instance.event.category in person_rate:
                            hourly_rate = person_rate[instance.event.category]
                            if entity_assignment.transaction is None:
                                entity_assignment.transaction = Transaction(
                                    amount=hourly_rate * instance.hours,
                                    reason=f"Trénování {instance.event} dne {occurrence_date}",
                                    date_due=occurrence_date + timedelta(days=14),
                                    person=entity_assignment.person,
                                    event=instance.event,
                                )
                            elif not entity_assignment.transaction.is_settled:
                                entity_assignment.transaction.amount = (
                                    hourly_rate * instance.hours
                                )

                            if commit:
                                entity_assignment.transaction.save()

                else:
                    entity_assignment.state = TrainingAttendance.UNEXCUSED
                    if (
                        type(entity_assignment) is CoachOccurrenceAssignment
                        and entity_assignment.transaction is not None
                        and not entity_assignment.transaction.is_settled
                    ):
                        entity_assignment.transaction.delete()
                        entity_assignment.transaction = None
                if commit:
                    entity_assignment.save()

        if commit:
            instance.save()
        return instance


class ReopenTrainingOccurrenceForm(ReopenOccurrenceMixin, ModelForm):
    class Meta:
        model = TrainingOccurrence
        fields = []

    def save(self, commit=True):
        instance = super().save(False)
        instance.state = EventOrOccurrenceState.OPEN

        present_coach_assignments = CoachOccurrenceAssignment.objects.filter(
            occurrence=instance, state=TrainingAttendance.PRESENT
        )
        for present_coach_assignment in present_coach_assignments:
            if present_coach_assignment.transaction is not None:
                present_coach_assignment.transaction.delete()
                present_coach_assignment.transaction = None

        observed_unexcused_assignments = [
            TrainingParticipantAttendance.objects.filter(
                occurrence=instance, state=TrainingAttendance.UNEXCUSED
            ),
            CoachOccurrenceAssignment.objects.filter(
                occurrence=instance, state=TrainingAttendance.UNEXCUSED
            ),
        ]

        for unexcused_assignments in observed_unexcused_assignments:
            for assignment in unexcused_assignments:
                assignment.state = TrainingAttendance.PRESENT
                if commit:
                    assignment.save()

        if commit:
            instance.save()
        return instance
