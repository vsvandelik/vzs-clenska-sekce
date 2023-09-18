from datetime import timedelta

from django import forms
from django.core.validators import MinValueValidator
from django.db.models import Q
from django.forms import ModelForm, CheckboxSelectMultiple, Form
from django_select2.forms import Select2Widget

from events.forms import MultipleChoiceFieldNoValidation
from events.forms_bases import (
    EventForm,
    EnrollMyselfParticipantForm,
    BulkApproveParticipantsForm,
    ActivePersonFormMixin,
    EventFormMixin,
    OrganizerAssignmentForm,
    OrganizerEnrollMyselfForm,
    OccurrenceFormMixin,
    EnrollMyselfOrganizerOccurrenceForm,
    UnenrollMyselfOccurrenceForm,
)
from events.forms_bases import ParticipantEnrollmentForm
from events.models import (
    EventOrOccurrenceState,
    ParticipantEnrollment,
    EventPositionAssignment,
)
from events.utils import parse_czech_date
from persons.models import Person
from persons.widgets import PersonSelectWidget
from .models import (
    OneTimeEvent,
    OneTimeEventOccurrence,
    OneTimeEventParticipantEnrollment,
    OrganizerOccurrenceAssignment,
    OneTimeEventParticipantAttendance,
    OneTimeEventAttendance,
)


class OneTimeEventForm(EventForm):
    class Meta(EventForm.Meta):
        model = OneTimeEvent
        fields = ["default_participation_fee"] + EventForm.Meta.fields
        widgets = EventForm.Meta.widgets | {
            "participants_enroll_state": Select2Widget(
                attrs={"onchange": "participantsEnrollListChanged()"}
            )
        }

    dates = MultipleChoiceFieldNoValidation(widget=CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        self.hours = kwargs.pop("request").POST.getlist("hours")
        super().__init__(*args, **kwargs)

    def _check_date_constraints(self):
        if self.cleaned_data["date_start"] > self.cleaned_data["date_end"]:
            self.add_error(
                "date_end", "Konec události nesmí být dříve než její začátek"
            )

    def _add_validate_occurrences(self):
        occurrences = []
        dates = self.cleaned_data.pop("dates")
        hours = self.hours
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

    def _check_participation_fee(self):
        if (
            self.cleaned_data["participants_enroll_state"]
            == ParticipantEnrollment.State.APPROVED
        ):
            if self.cleaned_data["default_participation_fee"] is None:
                self.add_error(
                    "default_participation_fee", "Toto pole musí být vyplněno"
                )

    def clean(self):
        self.cleaned_data = super().clean()
        self._check_participation_fee()
        self._check_date_constraints()
        self._add_validate_occurrences()
        return self.cleaned_data

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
            date_start += timedelta(days=1)
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


class TrainingCategoryForm(ModelForm):
    class Meta:
        model = OneTimeEvent
        fields = ["training_category"]
        widgets = {"training_category": Select2Widget()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["training_category"].required = False


class OneTimeEventParticipantEnrollmentUpdateAttendanceProvider:
    def update_attendance(self, instance):
        for occurrence in instance.event.eventoccurrence_set.all():
            if instance.state == ParticipantEnrollment.State.APPROVED:
                OneTimeEventParticipantAttendance(
                    enrollment=instance,
                    person=instance.person,
                    occurrence=occurrence,
                    state=OneTimeEventAttendance.PRESENT,
                ).save()
            else:
                attendance = OneTimeEventParticipantAttendance.objects.filter(
                    occurrence=occurrence, person=instance.person
                ).first()
                if attendance is not None:
                    attendance.delete()


class OneTimeEventEnrollmentApprovedHooks(
    OneTimeEventParticipantEnrollmentUpdateAttendanceProvider
):
    def approved_hooks(self, instance, event):
        if instance.transaction is not None:
            if not instance.transaction.is_settled:
                instance.transaction.amount = -instance.agreed_participation_fee
            else:
                instance.agreed_participation_fee = -instance.transaction.amount
        elif instance.agreed_participation_fee:
            instance.transaction = (
                OneTimeEventParticipantEnrollment.create_attached_transaction(
                    instance, event
                )
            )

    def save_enrollment(self, instance):
        if instance.transaction is not None:
            instance.transaction.save()
        instance.save()
        super().update_attendance(instance)


class OneTimeEventParticipantEnrollmentForm(
    ParticipantEnrollmentForm, OneTimeEventEnrollmentApprovedHooks
):
    class Meta(ParticipantEnrollmentForm.Meta):
        model = OneTimeEventParticipantEnrollment
        fields = ["agreed_participation_fee"] + ParticipantEnrollmentForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.event.default_participation_fee is not None:
            self.fields["agreed_participation_fee"].widget.attrs[
                "value"
            ] = self.event.default_participation_fee
        if (
            self.instance.transaction is not None
            and self.instance.transaction.is_settled
        ):
            self.fields["agreed_participation_fee"].widget.attrs["readonly"] = True

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data["state"] == ParticipantEnrollment.State.APPROVED.value
            and cleaned_data["agreed_participation_fee"] is None
        ):
            self.add_error("agreed_participation_fee", "Toto pole musí být vyplněno")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)

        if instance.state == ParticipantEnrollment.State.APPROVED:
            super().approved_hooks(instance, self.event)
        else:
            instance.agreed_participation_fee = None
            if instance.transaction is not None and not instance.transaction.is_settled:
                instance.transaction.delete()
                instance.transaction = None

        if commit:
            super().save_enrollment(instance)
        return instance


class OneTimeEventEnrollMyselfParticipantForm(
    EnrollMyselfParticipantForm,
    OneTimeEventParticipantEnrollmentUpdateAttendanceProvider,
):
    class Meta(EnrollMyselfParticipantForm.Meta):
        model = OneTimeEventParticipantEnrollment

    def save(self, commit=True):
        instance = super().save(False)

        fee = None
        if self.event.participants_enroll_state == ParticipantEnrollment.State.APPROVED:
            fee = self.event.default_participation_fee

        instance.one_time_event = self.event
        instance.agreed_participation_fee = fee

        if (
            self.event.participants_enroll_state == ParticipantEnrollment.State.APPROVED
            and self.event.can_person_enroll_as_participant(self.person)
        ):
            instance.state = ParticipantEnrollment.State.APPROVED
        else:
            instance.state = ParticipantEnrollment.State.SUBSTITUTE

        if (
            self.event.participants_enroll_state == ParticipantEnrollment.State.APPROVED
            and instance.agreed_participation_fee
        ):
            transaction = OneTimeEventParticipantEnrollment.create_attached_transaction(
                instance, self.event
            )
            if commit:
                transaction.save()
                instance.transaction = transaction

        if commit:
            instance.save()
            super().update_attendance(instance)

        return instance


class OrganizerOccurrenceAssignmentForm(OccurrenceFormMixin, OrganizerAssignmentForm):
    class Meta(OrganizerAssignmentForm.Meta):
        model = OrganizerOccurrenceAssignment

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop("person", None)
        super().__init__(*args, **kwargs)

        if self.instance.id is not None:
            self.fields["person"].widget.attrs["disabled"] = True
        else:
            self.fields["person"].queryset = Person.objects.filter(
                ~Q(organizeroccurrenceassignment__occurrence=self.occurrence)
            )
        self.fields[
            "position_assignment"
        ].queryset = self.occurrence.event.eventpositionassignment_set.all()

    def save(self, commit=True):
        instance = super().save(False)
        instance.occurrence = self.occurrence
        instance.state = OneTimeEventAttendance.PRESENT
        if instance.id is not None:
            instance.person = self.person
        if commit:
            instance.save()
        return instance


class BulkDeleteOrganizerFromOneTimeEventForm(EventFormMixin, Form):
    person = forms.IntegerField(
        label="Osoba",
        widget=PersonSelectWidget(attrs={"onchange": "personChanged(this)"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["person"].widget.queryset = Person.objects.filter(
            organizeroccurrenceassignment__occurrence__event=self.event
        ).distinct()

    def clean(self):
        cleaned_data = super().clean()

        person_pk = cleaned_data["person"]

        person = Person.objects.filter(pk=person_pk).first()

        if person is None:
            self.add_error("person", f"Osoba s id {person} neexistuje")

        cleaned_data["person"] = person
        return cleaned_data


class BulkAddOrganizerToOneTimeEventMixin(EventFormMixin):
    def _clean_parse_occurrences(self):
        occurrences = []
        occurrences_ids = []
        for occurrence_id_str in self.cleaned_data["occurrences"]:
            try:
                occurrence_id_int = int(occurrence_id_str)
                occurrence = OneTimeEventOccurrence.objects.get(pk=occurrence_id_int)
                occurrences.append(occurrence)
                occurrences_ids.append(occurrence_id_int)
            except (ValueError, OneTimeEventOccurrence.DoesNotExist):
                self.add_error(None, f"Vybrán neplatný den {occurrence_id_str}")
        self.cleaned_data["occurrences"] = occurrences
        self.cleaned_data["occurrences_ids"] = occurrences_ids

    def clean(self):
        self.cleaned_data = super().clean()
        self._clean_parse_occurrences()
        return self.cleaned_data

    def checked_occurrences(self):
        if hasattr(self, "cleaned_data") and "occurrences_ids" in self.cleaned_data:
            return self.cleaned_data["occurrences_ids"]
        return self.event.eventoccurrence_set.all().values_list("id", flat=True)

    def save(self, commit):
        instance = super().save(False)
        instance.state = OneTimeEventAttendance.PRESENT
        if commit:
            instance.save()
        return instance


class BulkAddOrganizerToOneTimeEventForm(
    BulkAddOrganizerToOneTimeEventMixin, OrganizerAssignmentForm
):
    occurrences = MultipleChoiceFieldNoValidation(widget=CheckboxSelectMultiple)

    class Meta(OrganizerAssignmentForm.Meta):
        model = OrganizerOccurrenceAssignment

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["person"].queryset = Person.objects.filter(
            ~Q(organizeroccurrenceassignment__occurrence__event=self.event)
        ).all()
        self.fields[
            "position_assignment"
        ].queryset = self.event.eventpositionassignment_set.all()

    def save(self, commit=True):
        instance = super().save(False)
        for occurrence in self.cleaned_data["occurrences"]:
            instance.pk = None
            instance.id = None
            instance.occurrence = occurrence
            if commit:
                instance.save()
        return instance


class OneTimeEventBulkApproveParticipantsForm(
    OneTimeEventEnrollmentApprovedHooks, BulkApproveParticipantsForm
):
    class Meta(BulkApproveParticipantsForm.Meta):
        model = OneTimeEvent

    agreed_participation_fee = forms.IntegerField(
        label="Poplatek za účast*",
        validators=[MinValueValidator(0)],
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        event = self.instance
        if cleaned_data["agreed_participation_fee"] is None:
            if event.default_participation_fee is not None:
                cleaned_data[
                    "agreed_participation_fee"
                ] = event.default_participation_fee
            else:
                self.add_error(
                    "agreed_participation_fee", "Toto pole musí být vyplněno"
                )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        cleaned_data = self.cleaned_data
        fee = cleaned_data["agreed_participation_fee"]
        enrollments_2_approve = instance.substitute_enrollments_2_capacity()

        for enrollment in enrollments_2_approve:
            enrollment.agreed_participation_fee = fee
            enrollment.state = ParticipantEnrollment.State.APPROVED
            super().approved_hooks(enrollment, instance)
            if commit:
                super().save_enrollment(enrollment)

        cleaned_data["count"] = len(enrollments_2_approve)
        return instance


class OneTimeEventEnrollMyselfOrganizerOccurrenceForm(
    EnrollMyselfOrganizerOccurrenceForm
):
    class Meta(EnrollMyselfOrganizerOccurrenceForm.Meta):
        model = OrganizerOccurrenceAssignment

    def save(self, commit=True):
        instance = super().save(False)
        instance.state = OneTimeEventAttendance.PRESENT
        if commit:
            instance.save()
        return instance


class OneTimeEventUnenrollMyselfOrganizerOccurrenceForm(UnenrollMyselfOccurrenceForm):
    class Meta(UnenrollMyselfOccurrenceForm.Meta):
        model = OrganizerOccurrenceAssignment


class OneTimeEventUnenrollMyselfOrganizerForm(
    ActivePersonFormMixin, EventFormMixin, Form
):
    def clean(self):
        cleaned_data = super().clean()
        observed_assignments = OrganizerOccurrenceAssignment.objects.filter(
            occurrence__event=self.event, person=self.person
        )
        for assignment in observed_assignments:
            if not assignment.can_unenroll():
                self.add_error(
                    None,
                    f"Z pozice {assignment.position_assignment.position} se již nemůžete odhlásit",
                )

        cleaned_data["assignments_2_delete"] = observed_assignments
        return cleaned_data


class OneTimeEventEnrollMyselfOrganizerForm(
    ActivePersonFormMixin,
    BulkAddOrganizerToOneTimeEventMixin,
    OrganizerEnrollMyselfForm,
):
    occurrences = MultipleChoiceFieldNoValidation(widget=CheckboxSelectMultiple)

    class Meta(OrganizerEnrollMyselfForm.Meta):
        model = OrganizerOccurrenceAssignment

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        positions = self.event.eventpositionassignment_set.all()
        can_enroll_positions_ids = []
        for position in positions:
            for occurrence in self.event.eventoccurrence_set.all():
                if occurrence.can_enroll_position(self.person, position):
                    can_enroll_positions_ids.append(position.id)
                    break
        self.fields[
            "position_assignment"
        ].queryset = EventPositionAssignment.objects.filter(
            id__in=can_enroll_positions_ids
        )

    def clean(self):
        cleaned_data = super().clean()
        position_assignment = cleaned_data.get("position_assignment")
        for occurrence in cleaned_data["occurrences"]:
            if position_assignment is not None and not occurrence.can_enroll_position(
                self.person, position_assignment
            ):
                self.add_error(
                    None, "Není možné se přihlásit na vybranou kombinací dnů a pozice"
                )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        instance.person = self.person
        for occurrence in self.cleaned_data["occurrences"]:
            instance.pk = None
            instance.id = None
            instance.occurrence = occurrence
            if commit:
                instance.save()
        return instance
