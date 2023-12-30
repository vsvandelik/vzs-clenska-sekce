from datetime import timedelta, timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML
from django import forms
from django.db.models import Q, QuerySet
from django.forms import ModelForm, Form, ChoiceField, IntegerField, ModelChoiceField
from django.utils import timezone
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _

from events.forms import MultipleChoiceFieldNoValidation
from events.forms_bases import (
    ActivePersonFormMixin,
    BulkApproveParticipantsForm,
    EnrollMyselfOrganizerOccurrenceForm,
    EnrollMyselfParticipantForm,
    EventForm,
    EventFormMixin,
    OccurrenceFormMixin,
    OrganizerAssignmentForm,
    ParticipantEnrollmentForm,
    PersonMetaMixin,
    ReopenOccurrenceMixin,
    UnenrollMyselfOccurrenceForm,
)
from events.models import EventOrOccurrenceState, ParticipantEnrollment
from events.utils import parse_czech_date
from persons.models import Person, PersonHourlyRate
from trainings.utils import (
    day_shortcut_2_weekday,
    days_shortcut_list,
    weekday_2_day_shortcut,
    TrainingsFilter,
)
from transactions.models import Transaction
from vzs import settings
from vzs.forms import WithoutFormTagFormHelper
from vzs.utils import (
    combine_date_and_time,
    date_pretty,
    send_notification_email,
    time_pretty,
    filter_queryset,
)
from vzs.widgets import TimePickerWithIcon
from .models import (
    CoachOccurrenceAssignment,
    CoachPositionAssignment,
    Training,
    TrainingAttendance,
    TrainingOccurrence,
    TrainingParticipantAttendance,
    TrainingParticipantEnrollment,
    TrainingReplaceabilityForParticipants,
    TrainingWeekdays,
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
            training_dates = [parse_czech_date(x) for x in self.cleaned_data["day"]]
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

        datetime_start = combine_date_and_time(date, time_from)
        datetime_end = combine_date_and_time(date, time_to)

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
                parse_czech_date(date_raw) for date_raw in self.cleaned_data["day"]
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


class TrainingEnrollmentStateChangedSendMailProvider:
    def enrollment_state_changed_send_mail(self, enrollment):
        if enrollment.state == ParticipantEnrollment.State.APPROVED:
            send_notification_email(
                _("Změna stavu přihlášky"),
                _(f"Vaše přihláška na trénink {enrollment.event} byla schválena"),
                [enrollment.person],
            )
        elif enrollment.state == ParticipantEnrollment.State.SUBSTITUTE:
            send_notification_email(
                _("Změna stavu přihlášky"),
                _(
                    f"Vaší přihlášce na trénink {enrollment.event} byl změněn stav na NÁHRADNÍK"
                ),
                [enrollment.person],
            )
        elif enrollment.state == ParticipantEnrollment.State.REJECTED:
            send_notification_email(
                _("Odmítnutí účasti"),
                _(f"Na tréninku {enrollment.event} vám byla zakázána účast"),
                [enrollment.person],
            )
        else:
            raise NotImplementedError


class TrainingParticipantEnrollmentForm(
    TrainingWeekdaysSelectionMixin,
    ParticipantEnrollmentForm,
    TrainingEnrollmentStateChangedSendMailProvider,
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
                super().enrollment_state_changed_send_mail(instance)
            else:
                old_instance = TrainingParticipantEnrollment.objects.get(id=instance.id)
                if old_instance.state != instance.state:
                    super().enrollment_state_changed_send_mail(instance)
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
    TrainingEnrollmentStateChangedSendMailProvider,
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

        super().enrollment_state_changed_send_mail(instance)
        if commit:
            instance.save()
            super().initialize_weekdays(instance, weekdays)
            instance.save()
            super().participant_enrollment_update_attendance(instance)
        return instance


class CoachAssignmentForm(
    EventFormMixin,
    CoachAssignmentUpdateAttendanceProvider,
    OrganizerAssignmentForm,
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
            if self.event.main_coach_assignment is not None:
                self._no_longer_main_coach_send_mail(self.event.main_coach_assignment)
            self.event.main_coach_assignment = instance
        elif (
            self.event.main_coach_assignment is not None
            and instance.person == self.event.main_coach_assignment.person
        ):
            self.event.main_coach_assignment = None

        if instance.id is None:
            self._assigned_send_mail(instance)
        else:
            old_instance = CoachPositionAssignment.objects.get(id=instance.id)
            if (
                old_instance.position_assignment != instance.position_assignment
                or old_instance.is_main_coach() != instance.is_main_coach()
            ):
                self._assignment_changed_send_mail(instance, old_instance)

        if commit:
            super().coach_assignment_update_attendance(instance, self.event)
            instance.save()
            self.event.save()
        return instance

    def _assigned_send_mail(self, assignment):
        main_coach_txt = ""
        if assignment.is_main_coach():
            main_coach_txt = "garantující"
        send_notification_email(
            _("Přihlášení trenéra"),
            _(
                f"Byl(a) jste přihlášen jako {main_coach_txt} trenér na pozici {assignment.position_assignment.position} na trénink {assignment.training}"
            ),
            [assignment.person],
        )

    def _no_longer_main_coach_send_mail(self, assignment):
        send_notification_email(
            _("Úprava garanta tréninku"),
            _(f"Byl vám odebrán status garanta tréninku {assignment.training}"),
            [assignment.person],
        )

    def _assignment_changed_send_mail(self, new_assignment, old_assignment):
        old_main_coach = "ANO" if old_assignment.is_main_coach() else "NE"
        new_main_coach = "ANO" if new_assignment.is_main_coach() else "NE"
        send_notification_email(
            _("Úprava přihlášky trenéra"),
            _(
                f"Vaše přihláška na trenéra události {new_assignment.training} byla upravena. Pozice: {old_assignment.position_assignment.position} --> {new_assignment.position_assignment.position}, garant: {old_main_coach} --> {new_main_coach}"
            ),
            [new_assignment.person],
        )


class CoachAssignmentDeleteForm(ModelForm):
    class Meta:
        model = CoachPositionAssignment
        fields = []

    def save(self, commit=True):
        instance = super().save(False)
        self._assignment_delete_send_mail(instance)
        if commit:
            CoachOccurrenceAssignment.objects.filter(
                person=instance.person, occurrence__event=instance.training
            ).delete()
            instance.delete()
        return instance

    def _assignment_delete_send_mail(self, assignment):
        send_notification_email(
            _("Zrušení trenéra"),
            _(
                f"Byl(a) jste odebrán(a) z trenérské pozice {assignment.position_assignment.position} události {assignment.training}"
            ),
            [assignment.person],
        )


class TrainingBulkApproveParticipantsForm(
    TrainingParticipantEnrollmentUpdateAttendanceProvider,
    TrainingEnrollmentStateChangedSendMailProvider,
    BulkApproveParticipantsForm,
):
    class Meta(BulkApproveParticipantsForm.Meta):
        model = Training

    def save(self, commit=True):
        instance = super().save(False)
        enrollments_2_approve = instance.substitute_enrollments_2_capacity()

        for enrollment in enrollments_2_approve:
            enrollment.state = ParticipantEnrollment.State.APPROVED
            super().enrollment_state_changed_send_mail(enrollment)
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

    def save(self, commit=True):
        instance = super().save(False)
        self._cancel_excuse_send_mail(instance)
        if commit:
            instance.save()
        return instance

    def _cancel_excuse_send_mail(self, assignment):
        send_notification_email(
            _("Zrušení omluvenky trenéra"),
            _(
                f"Vaše omluvení neúčasti dne {date_pretty(assignment.occurrence.datetime_start)} tréninku {assignment.occurrence.event} bylo zrušeno administrátorem"
            ),
            [assignment.person],
        )


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


class TrainingPositionFreeSpotSendMailProvider:
    def offer_free_training_position_send_mail(self, assignment):
        category = assignment.occurrence.event.category
        recipients = []
        hourly_rates = PersonHourlyRate.objects.filter(event_type=category)
        for hourly_rate in hourly_rates:
            if (
                hourly_rate.person == assignment.person
                or not assignment.occurrence.can_enroll_position(
                    hourly_rate.person, assignment.position_assignment
                )
            ):
                continue
            recipients.append(hourly_rate.person)

        send_notification_email(
            _("Nabídka volné trenérské pozice"),
            _(
                f"Jednorázově se uvolnila trenérská pozice {assignment.position_assignment.position} na tréninku {assignment.occurrence.event} dne {date_pretty(assignment.occurrence.datetime_start)} od {time_pretty(assignment.occurrence.datetime_start)} do {time_pretty(assignment.occurrence.datetime_end)}"
            ),
            recipients,
        )


class ExcuseMyselfCoachForm(TrainingPositionFreeSpotSendMailProvider, ExcuseCoachForm):
    class Meta(ExcuseCoachForm.Meta):
        pass

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.occurrence.can_coach_excuse(self.instance.person):
            self.add_error(None, "Již se není možné odhlásit z trenérské pozice")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        self._excuse_myself_send_mail(instance)
        if commit:
            instance.save()
        super().offer_free_training_position_send_mail(instance)
        return instance

    def _excuse_myself_send_mail(self, assignment):
        send_notification_email(
            _("Omluvení neúčasti trenéra"),
            _(
                f"Potvrzujeme nahlášení neúčasti dne {date_pretty(assignment.occurrence.datetime_start)} tréninku {assignment.occurrence.event}"
            ),
            [assignment.person],
        )


class CoachExcuseForm(TrainingPositionFreeSpotSendMailProvider, ExcuseCoachForm):
    class Meta(ExcuseCoachForm.Meta):
        pass

    def save(self, commit=True):
        instance = super().save(False)
        self._excuse_coach_send_mail(instance)
        if commit:
            instance.save()
        super().offer_free_training_position_send_mail(instance)
        return instance

    def _excuse_coach_send_mail(self, assignment):
        send_notification_email(
            _("Omluvení neúčasti trenéra"),
            _(
                f"Administrátor zaevidoval vaši neúčast dne {date_pretty(assignment.occurrence.datetime_start)} tréninku {assignment.occurrence.event}"
            ),
            [assignment.person],
        )


class TrainingEnrollMyselfOrganizerOccurrenceForm(EnrollMyselfOrganizerOccurrenceForm):
    class Meta(EnrollMyselfOrganizerOccurrenceForm.Meta):
        model = CoachOccurrenceAssignment

    def save(self, commit=True):
        instance = super().save(False)
        instance.state = TrainingAttendance.PRESENT
        self._one_time_assignment_created(instance)
        if commit:
            instance.save()
        return instance

    def _one_time_assignment_created(self, assignment):
        send_notification_email(
            _("Jednorázová trenérská účast"),
            _(
                f"Potvrzujeme vaši přihlášku jako jednorázový trenér na pozici {assignment.position_assignment.position} dne {date_pretty(assignment.occurrence.datetime_start)} tréninku {assignment.occurrence.event}"
            ),
            [assignment.person],
        )


class TrainingUnenrollMyselfOrganizerFromOccurrenceForm(UnenrollMyselfOccurrenceForm):
    class Meta(UnenrollMyselfOccurrenceForm.Meta):
        model = CoachOccurrenceAssignment

    def save(self, commit=True):
        instance = super().save(False)
        self._one_time_assignment_deleted(instance)
        if commit:
            instance.delete()
        return instance

    def _one_time_assignment_deleted(self, assignment):
        send_notification_email(
            _("Zrušení jednorázové účasti trenéra"),
            _(
                f"Vaše jednorázová trenérská účast na pozici {assignment.position_assignment.position} dne {date_pretty(assignment.occurrence.datetime_start)} tréninku {assignment.occurrence.event} byla zrušena na vlastní žádost"
            ),
            [assignment.person],
        )


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
            old_instance = CoachOccurrenceAssignment.objects.get(id=instance.id)
            if (
                old_instance.position_assignment.position
                != instance.position_assignment.position
            ):
                self._one_time_coach_edit_send_mail(instance, old_instance)
        else:
            self._new_one_time_coach_added_send_mail(instance)
        if commit:
            instance.save()
        return instance

    def _new_one_time_coach_added_send_mail(self, assignment):
        send_notification_email(
            _("Jednorázová trenérská účast"),
            _(
                f"Byl(a) jste přidán(a) jako jednorázový trenér na pozici {assignment.position_assignment.position} dne {date_pretty(assignment.occurrence.datetime_start)} tréninku {assignment.occurrence.event} administrátorem"
            ),
            [assignment.person],
        )

    def _one_time_coach_edit_send_mail(self, new_assignment, old_assignment):
        send_notification_email(
            _("Úprava jednorázové trenérské účasti"),
            _(
                f"Vaše přihláška na jednorázového trenéra dne {date_pretty(new_assignment.occurrence.datetime_start)} tréninku byla upravena: pozice {old_assignment.position_assignment.position} --> {new_assignment.position_assignment.position}"
            ),
            [new_assignment.person],
        )


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

    def save(self, commit=True):
        instance = super().save(False)
        self._excuse_participant_send_mail(instance)
        if commit:
            instance.save()
        return instance

    def _excuse_participant_send_mail(self, attendance):
        send_notification_email(
            _("Omluvení neúčasti účastníka"),
            _(
                f"Administrátor zaevidoval vaši neúčast dne {date_pretty(attendance.occurrence.datetime_start)} tréninku {attendance.occurrence.event}"
            ),
            [attendance.person],
        )


class CancelParticipantExcuseForm(CancelExcuseForm):
    class Meta(CancelExcuseForm.Meta):
        model = TrainingParticipantAttendance

    def save(self, commit=True):
        instance = super().save(False)
        self._cancel_excuse_send_mail(instance)
        if commit:
            instance.save()
        return instance

    def _cancel_excuse_send_mail(self, attendance):
        send_notification_email(
            _("Zrušení omluvenky účastníka"),
            _(
                f"Vaše omluvení neúčasti dne {date_pretty(attendance.occurrence.datetime_start)} tréninku {attendance.occurrence.event} bylo zrušeno administrátorem"
            ),
            [attendance.person],
        )


class ExcuseMyselfParticipantForm(ExcuseParticipantForm):
    class Meta(ExcuseParticipantForm.Meta):
        pass

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.occurrence.can_participant_excuse(self.instance.person):
            self.add_error(None, "Již se není možné odhlásit jako účastník")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        self._excuse_myself_send_mail(instance)
        if commit:
            instance.save()
        return instance

    def _excuse_myself_send_mail(self, attendance):
        send_notification_email(
            _("Omluvení neúčasti účastníka"),
            _(
                f"Potvrzujeme nahlášení neúčasti dne {date_pretty(attendance.occurrence.datetime_start)} tréninku {attendance.occurrence.event}"
            ),
            [attendance.person],
        )


class TrainingUnenrollMyselfParticipantFromOccurrenceForm(UnenrollMyselfOccurrenceForm):
    class Meta(UnenrollMyselfOccurrenceForm.Meta):
        model = TrainingParticipantAttendance

    def save(self, commit=True):
        instance = super().save(False)
        self._one_time_attendance_deleted(instance)
        if commit:
            instance.delete()
        return instance

    def _one_time_attendance_deleted(self, attendance):
        send_notification_email(
            _("Zrušení jednorázové účasti účastníka"),
            _(
                f"Vaše jednorázová účast dne {date_pretty(attendance.occurrence.datetime_start)} tréninku {attendance.occurrence.event} byla zrušena na vlastní žádost"
            ),
            [attendance.person],
        )


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
        self._new_one_time_participant_added_send_mail(instance)
        if instance.id is not None:
            instance.person = self.person
        if commit:
            instance.save()
        return instance

    def _new_one_time_participant_added_send_mail(self, attendance):
        send_notification_email(
            _("Jednorázová účast účastníka"),
            _(
                f"Byl(a) jste přidán(a) jako jednorázový účastník dne {date_pretty(attendance.occurrence.datetime_start)} tréninku {attendance.occurrence.event} administrátorem"
            ),
            [attendance.person],
        )


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
        self._one_time_attendance_created(instance)
        if commit:
            instance.save()
        return instance

    def _one_time_attendance_created(self, attendance):
        send_notification_email(
            _("Jednorázová účast na tréninku"),
            _(
                f"Potvrzujeme vaši přihlášku jako jednorázový účastník dne {date_pretty(attendance.occurrence.datetime_start)} tréninku {attendance.occurrence.event}"
            ),
            [attendance.person],
        )


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
                        occurrence_date = localdate(instance.datetime_start)
                        person_rates = PersonHourlyRate.get_person_hourly_rates(
                            entity_assignment.person
                        )
                        if instance.event.category in person_rates:
                            hourly_rate = person_rates[instance.event.category]
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
        self._check_repeating_absence(instance)
        return instance

    def _check_repeating_absence(self, occurrence):
        event = occurrence.event
        sorted_occurrences = event.sorted_occurrences_list()
        idx = self._index(sorted_occurrences, occurrence)
        for (
            participant_attendance
        ) in occurrence.trainingparticipantattendance_set.all():
            absence_count = self._count_participant_absence_in_row(
                participant_attendance.person, sorted_occurrences, idx
            )
            if (
                absence_count >= settings.MIN_PARTICIPANT_ABSENCE_SEND_MAIL
                and event.main_coach_assignment is not None
            ):
                send_notification_email(
                    _("Opakovaná absence účastníka tréninku"),
                    _(
                        f"Na tréninku {event}, kde jste garantujícím trenérem, byl účastník {participant_attendance.person} {absence_count}x za sebou nepřítomen"
                    ),
                    [event.main_coach_assignment.person],
                )

    def _count_participant_absence_in_row(self, person, sorted_occurrences, stop_idx):
        idx = stop_idx
        count = 0
        while idx >= 0:
            occurrence = sorted_occurrences[idx]
            participant_attendance = (
                occurrence.trainingparticipantattendance_set.filter(
                    person=person
                ).first()
            )
            if participant_attendance is not None:
                if participant_attendance.state != TrainingAttendance.PRESENT:
                    count += 1
                else:
                    return count
            idx -= 1
        return count

    def _index(self, polymorphic_queryset, item):
        for i in range(len(polymorphic_queryset)):
            if polymorphic_queryset[i] == item:
                return i
        return -1


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


class TrainingsFilterForm(Form):
    category = ChoiceField(
        label=_("Typ tréninku"),
        required=False,
        choices=[("", "---------")] + Training.Category.choices,
    )
    year_start = IntegerField(label=_("Rok začátku"), required=False, min_value=2000)
    main_coach = ModelChoiceField(label=_("Garant"), required=False, queryset=None)
    only_opened = ChoiceField(
        label=_("Pouze neukončené"),
        required=False,
        choices=[("yes", "Ano"), ("no", "Ne")],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = self._create_form_helper()

        self.fields["main_coach"].queryset = (
            Person.objects.filter(
                coachpositionassignment__main_coach_assignment__isnull=False
            )
            .distinct()
            .order_by("last_name", "first_name")
            .all()
        )

    @staticmethod
    def _create_form_helper():
        helper = FormHelper()

        helper.form_method = "GET"
        helper.form_id = "trainings-filter-form"
        helper.include_media = False
        helper.layout = Layout(
            Div(
                Div(
                    Div("category", css_class="col-md-4"),
                    Div("year_start", css_class="col-md-2"),
                    Div("main_coach", css_class="col-md-4"),
                    Div("only_opened", css_class="col-md-2"),
                    css_class="row",
                ),
                Div(
                    Div(
                        HTML(
                            "<a href='.' class='btn btn-secondary ml-1 float-right'>Zrušit</a>"
                        ),
                        Submit(
                            "submit",
                            "Filtrovat",
                            css_class="btn btn-primary float-right",
                        ),
                        css_class="col-12",
                    ),
                    css_class="row",
                ),
                css_class="p-2 border rounded bg-light",
                style="box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.05);",
            )
        )

        return helper

    def process_filter(self, trainings) -> QuerySet[Training]:
        return filter_queryset(
            trainings,
            self.cleaned_data if self.is_valid() else None,
            TrainingsFilter,
        )
