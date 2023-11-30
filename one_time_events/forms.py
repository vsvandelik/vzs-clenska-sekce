from datetime import timedelta

from django import forms
from django.core.validators import MinValueValidator
from django.db.models import Q
from django.forms import ModelForm, CheckboxSelectMultiple, Form
from django.utils.translation import gettext_lazy as _
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
    ReopenOccurrenceMixin,
    InsertRequestIntoSelf,
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
from transactions.models import Transaction
from vzs.forms import WithoutFormTagFormHelper
from vzs.utils import send_notification_email, date_pretty, payment_email_html
from .models import (
    OneTimeEvent,
    OneTimeEventOccurrence,
    OneTimeEventParticipantEnrollment,
    OrganizerOccurrenceAssignment,
    OneTimeEventParticipantAttendance,
    OneTimeEventAttendance,
)


class OneTimeEventParticipantEnrollmentUpdateAttendanceProvider:
    def participant_enrollment_update_attendance(self, instance, occurrences=None):
        if occurrences is None:
            occurrences = instance.event.eventoccurrence_set.all()

        for occurrence in occurrences:
            if instance.state == ParticipantEnrollment.State.APPROVED:
                OneTimeEventParticipantAttendance.objects.update_or_create(
                    occurrence=occurrence,
                    person=instance.person,
                    defaults={
                        "enrollment": instance,
                        "person": instance.person,
                        "occurrence": occurrence,
                        "state": OneTimeEventAttendance.PRESENT,
                    },
                )
            else:
                attendance = OneTimeEventParticipantAttendance.objects.filter(
                    occurrence=occurrence, person=instance.person
                ).first()
                if attendance is not None:
                    attendance.delete()


class OneTimeEventForm(
    OneTimeEventParticipantEnrollmentUpdateAttendanceProvider, EventForm
):
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

        self.helper = WithoutFormTagFormHelper()

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

        if commit:
            for child in children:
                occurrence = self._find_occurrence_with_date(child.date)
                if occurrence is not None:
                    if child.hours != occurrence[1]:
                        child.hours = occurrence[1]
                        child.save()
                    self.cleaned_data["occurrences"].remove(occurrence)
                else:
                    child.delete()

            for date, hours in occurrences:
                occurrence_obj = OneTimeEventOccurrence(
                    event=instance,
                    state=EventOrOccurrenceState.OPEN,
                    date=date,
                    hours=hours,
                )
                occurrence_obj.save()
                for (
                    participant_enrollment
                ) in instance.onetimeeventparticipantenrollment_set.all():
                    super().participant_enrollment_update_attendance(
                        participant_enrollment, [occurrence_obj]
                    )

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


class OneTimeEventEnrollmentSubstituteSendMailProvider:
    def enrollment_substitute_send_mail(self, enrollment):
        send_notification_email(
            _("Změna stavu přihlášky"),
            _(
                f"Vaší přihlášce na jednorázovou událost {enrollment.event} byl změněn stav na NÁHRADNÍK"
            ),
            [enrollment.person],
        )


class OneTimeEventEnrollmentApprovedHooks(
    OneTimeEventParticipantEnrollmentUpdateAttendanceProvider
):
    def approved_hooks(self, commit, instance, event):
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
        if commit:
            instance.transaction.save()
            old_instance = OneTimeEventParticipantEnrollment.objects.filter(
                id=instance.id
            ).first()
            if old_instance is not None and instance.state != old_instance.state:
                self._enrollment_approve_send_mail(instance)

    def save_enrollment(self, instance):
        instance.save()
        super().participant_enrollment_update_attendance(instance)

    def _enrollment_approve_send_mail(self, enrollment):
        payment_html = ""
        if not enrollment.transaction.is_settled:
            payment_html = "<br><br>" + payment_email_html(
                enrollment.transaction, self.request
            )
        send_notification_email(
            _("Schválení přihlášky"),
            _(
                f"Vaše přihláška na jednorázovou událost {enrollment.event} byla schválena{payment_html}"
            ),
            [enrollment.person],
        )


class OneTimeEventParticipantEnrollmentForm(
    InsertRequestIntoSelf,
    ParticipantEnrollmentForm,
    OneTimeEventEnrollmentSubstituteSendMailProvider,
    OneTimeEventEnrollmentApprovedHooks,
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
            self.fields["agreed_participation_fee"].widget.attrs["value"] = abs(
                self.instance.transaction.amount
            )

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
            super().approved_hooks(commit, instance, self.event)
        else:
            instance.agreed_participation_fee = None
            if (
                instance.id is None
                or instance.state
                != OneTimeEventParticipantEnrollment.objects.get(id=instance.id).state
            ):
                if instance.state == ParticipantEnrollment.State.SUBSTITUTE:
                    super().enrollment_substitute_send_mail(instance)
                else:
                    self._enrollment_refused_send_mail(instance)
            if instance.transaction is not None and not instance.transaction.is_settled:
                instance.transaction.delete()
                instance.transaction = None

        if commit:
            super().save_enrollment(instance)
        return instance

    def _enrollment_refused_send_mail(self, enrollment):
        send_notification_email(
            _("Odmítnutí účasti"),
            _(f"Na jednorázové události {enrollment.event} vám byla zakázána účast"),
            [enrollment.person],
        )


class OneTimeEventEnrollMyselfParticipantForm(
    EnrollMyselfParticipantForm,
    OneTimeEventEnrollmentSubstituteSendMailProvider,
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
            super().enrollment_substitute_send_mail(instance)

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
            super().participant_enrollment_update_attendance(instance)

        return instance


class OccurrenceOpenRestrictionMixin:
    def clean(self):
        cleaned_data = super().clean()
        if not self.occurrence.is_opened:
            self.add_error(None, "Tento den již není otevřen")
        return cleaned_data


class OrganizerOccurrenceAssignedSendMailProvider:
    def assigned_send_mail(self, organizer_assignment):
        send_notification_email(
            _("Přihlášení organizátora"),
            _(
                f"Byl(a) jste úspěšně přihlášen(a) jako {organizer_assignment.position_assignment.position} dne {organizer_assignment.occurrence.date} na události {organizer_assignment.occurrence.event}"
            ),
            [organizer_assignment.person],
        )


class OrganizerOccurrenceAssignmentForm(
    OccurrenceFormMixin,
    OrganizerOccurrenceAssignedSendMailProvider,
    OccurrenceOpenRestrictionMixin,
    OrganizerAssignmentForm,
):
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
            old_instance = OrganizerOccurrenceAssignment.objects.get(id=instance.id)
            if (
                old_instance.position_assignment.position
                != instance.position_assignment.position
            ):
                self._assignment_changed_send_mail(instance, old_instance)
        else:
            super().assigned_send_mail(instance)
        if commit:
            instance.save()
        return instance

    def _assignment_changed_send_mail(self, new_assignment, old_assignment):
        send_notification_email(
            _("Změna přihlášky organizátora"),
            _(
                f"Došlo ke změně organizátorské pozice, na kterou jste přihlášen(a): {old_assignment.position_assignment.position} --> {new_assignment.position_assignment.position} dne {new_assignment.occurrence.date} na události {new_assignment.occurrence.event}"
            ),
            [new_assignment.person],
        )


class BulkAddOrganizerSendMailProvider:
    def organizer_added_send_mail(self, occurrences, organizer_assignment):
        dates = []
        for occurrence in occurrences:
            dates.append(date_pretty(occurrence.date))
        dates_pretty = ", ".join(dates)

        send_notification_email(
            _("Přihlášení organizátora"),
            _(
                f"Byl(a) jste přihlášen jako organizátor na pozici {organizer_assignment.position_assignment} dny {dates_pretty} události {occurrences[0].event}"
            ),
            [organizer_assignment.person],
        )


class BulkDeleteOrganizerFromOneTimeEventForm(EventFormMixin, Form):
    person = forms.IntegerField(
        label="Osoba",
        widget=PersonSelectWidget(attrs={"onchange": "personChanged(this)"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["person"].widget.queryset = Person.objects.filter(
            organizeroccurrenceassignment__occurrence__event=self.event,
            organizeroccurrenceassignment__occurrence__state=EventOrOccurrenceState.OPEN,
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
    BulkAddOrganizerToOneTimeEventMixin,
    BulkAddOrganizerSendMailProvider,
    OrganizerAssignmentForm,
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
        cleaned_occurrences = self.cleaned_data["occurrences"]
        for occurrence in cleaned_occurrences:
            instance.pk = None
            instance.id = None
            instance.occurrence = occurrence
            if commit:
                instance.save()
        if cleaned_occurrences:
            super().organizer_added_send_mail(cleaned_occurrences, instance)
        return instance


class OneTimeEventBulkApproveParticipantsForm(
    InsertRequestIntoSelf,
    OneTimeEventEnrollmentApprovedHooks,
    BulkApproveParticipantsForm,
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
            super().approved_hooks(commit, enrollment, instance)
            if commit:
                super().save_enrollment(enrollment)

        cleaned_data["count"] = len(enrollments_2_approve)
        return instance


class OneTimeEventEnrollMyselfOrganizerOccurrenceForm(
    OrganizerOccurrenceAssignedSendMailProvider, EnrollMyselfOrganizerOccurrenceForm
):
    class Meta(EnrollMyselfOrganizerOccurrenceForm.Meta):
        model = OrganizerOccurrenceAssignment

    def save(self, commit=True):
        instance = super().save(False)
        instance.state = OneTimeEventAttendance.PRESENT
        if commit:
            instance.save()
        super().assigned_send_mail(instance)
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
    BulkAddOrganizerSendMailProvider,
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
        cleaned_occurrences = self.cleaned_data["occurrences"]
        for occurrence in cleaned_occurrences:
            instance.pk = None
            instance.id = None
            instance.occurrence = occurrence
            if commit:
                instance.save()
        if cleaned_occurrences:
            super().organizer_added_send_mail(cleaned_occurrences, instance)
        return instance


class CleanParseParticipantAssignmentsMixin:
    def clean(self):
        cleaned_data = super().clean()
        self._clean_parse_participants()
        return cleaned_data

    def _clean_parse_participants(self):
        participant_assignments = []
        for participant_assignment_id_str in self.participants:
            try:
                participant_assignment_id = int(participant_assignment_id_str)
            except ValueError:
                self.add_error(None, "Neplatná hodnota přiřazení účastníka")
                continue
            participant_assignment = OneTimeEventParticipantAttendance.objects.filter(
                id=participant_assignment_id
            ).first()
            if participant_assignment is None:
                self.add_error(None, "Neexistující účastník")
                continue
            participant_assignments.append(participant_assignment)
        self.cleaned_data["participants"] = participant_assignments


class CleanParseOrganizerAssignmentsMixin:
    def clean(self):
        cleaned_data = super().clean()
        self._clean_parse_organizers()
        return cleaned_data

    def _clean_parse_organizers(self):
        organizer_assignments = []
        for organizer_assignment_id_str in self.organizers:
            try:
                organizer_assignment_id = int(organizer_assignment_id_str)
            except ValueError:
                self.add_error(None, "Neplatná hodnota přiřazení organizátora")
                continue
            organizer_assignment = OrganizerOccurrenceAssignment.objects.filter(
                id=organizer_assignment_id
            ).first()
            if organizer_assignment is None:
                self.add_error(None, "Neexistující organizátor")
                continue
            organizer_assignments.append(organizer_assignment)
        self.cleaned_data["organizers"] = organizer_assignments


class OneTimeEventFillAttendanceForm(
    CleanParseParticipantAssignmentsMixin,
    CleanParseOrganizerAssignmentsMixin,
    ModelForm,
):
    class Meta:
        model = OneTimeEventOccurrence
        fields = []

    def __init__(self, *args, **kwargs):
        post = kwargs.pop("request").POST
        self.organizers = post.getlist("organizers")
        self.participants = post.getlist("participants")
        super().__init__(*args, **kwargs)

    def checked_participant_assignments(self):
        if hasattr(self, "cleaned_data") and "participants" in self.cleaned_data:
            return self.cleaned_data["participants"]
        if self.instance.is_opened:
            return OneTimeEventParticipantAttendance.objects.filter(
                occurrence=self.instance
            )
        return OneTimeEventParticipantAttendance.objects.filter(
            occurrence=self.instance, state=OneTimeEventAttendance.PRESENT
        )

    def checked_organizer_assignments(self):
        if hasattr(self, "cleaned_data") and "organizers" in self.cleaned_data:
            return self.cleaned_data["organizers"]
        if self.instance.is_opened:
            return OrganizerOccurrenceAssignment.objects.filter(
                occurrence=self.instance
            )

        return OrganizerOccurrenceAssignment.objects.filter(
            occurrence=self.instance, state=OneTimeEventAttendance.PRESENT
        )

    def save(self, commit=True):
        instance = super().save(False)

        self._change_state_to_closed(commit, instance)

        observed_assignments = [
            OneTimeEventParticipantAttendance.objects.filter(occurrence=instance),
            OrganizerOccurrenceAssignment.objects.filter(occurrence=instance),
        ]

        assignments = [
            self.cleaned_data["participants"],
            self.cleaned_data["organizers"],
        ]

        for i in range(0, 2):
            entity_assignments = observed_assignments[i]
            for entity_assignment in entity_assignments:
                if entity_assignment in assignments[i]:
                    entity_assignment.state = OneTimeEventAttendance.PRESENT
                else:
                    entity_assignment.state = OneTimeEventAttendance.MISSING
                if commit:
                    entity_assignment.save()
        if commit:
            instance.save()
        return instance

    def _change_state_to_closed(self, commit, occurrence):
        occurrence.state = EventOrOccurrenceState.CLOSED
        closed_occurrences_count = OneTimeEventOccurrence.objects.filter(
            Q(event=occurrence.event)
            & Q(
                Q(state=EventOrOccurrenceState.CLOSED)
                | Q(state=EventOrOccurrenceState.COMPLETED)
            )
        ).count()
        occurrences_count = occurrence.event.eventoccurrence_set.count()
        if closed_occurrences_count + 1 == occurrences_count:
            occurrence.event.state = EventOrOccurrenceState.CLOSED
            if commit:
                occurrence.event.save()


class ApproveOccurrenceForm(
    CleanParseParticipantAssignmentsMixin,
    CleanParseOrganizerAssignmentsMixin,
    ModelForm,
):
    class Meta:
        model = OneTimeEventOccurrence
        fields = []

    def __init__(self, *args, **kwargs):
        self.post = kwargs.pop("request").POST
        self.participants = self.post.getlist("participants")
        self.organizers = self.post.getlist("organizers")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        self._clean_parse_organizer_amounts()
        return cleaned_data

    def _clean_parse_organizer_amounts(self):
        organizer_amounts = {}
        for organizer_assignment in self.cleaned_data["organizers"]:
            key = f"{organizer_assignment.id}_organizer_amount"
            if key not in self.post:
                if (
                    organizer_assignment.transaction is not None
                    and organizer_assignment.transaction.is_settled
                ):
                    continue
                self.add_error(
                    None,
                    f"Chybí částka k proplacení organizátoru {organizer_assignment.person}",
                )
            else:
                amount_str = self.post[key]
                try:
                    amount = int(amount_str)
                except ValueError:
                    self.add_error(None, "Neplatná částka k vyplacení")
                    continue
                if amount < 0:
                    self.add_error(None, "Záporná částka k vyplacení organizátorovi")
                organizer_amounts[organizer_assignment.id] = amount
        self.cleaned_data["organizer_amounts"] = organizer_amounts

    def save(self, commit=True):
        instance = super().save(False)

        self._change_state_to_approve(commit, instance)
        self._update_participants_attendance(commit, instance)
        self._update_organizers_attendance_transaction(commit, instance)

        if commit:
            instance.save()
        return instance

    def _change_state_to_approve(self, commit, occurrence):
        occurrence.state = EventOrOccurrenceState.COMPLETED
        approved_occurrences_count = OneTimeEventOccurrence.objects.filter(
            event=occurrence.event, state=EventOrOccurrenceState.COMPLETED
        ).count()
        occurrences_count = occurrence.event.eventoccurrence_set.count()
        if approved_occurrences_count + 1 == occurrences_count:
            occurrence.event.state = EventOrOccurrenceState.COMPLETED
            if commit:
                occurrence.event.save()

    def _update_participants_attendance(self, commit, occurrence):
        for (
            participant_attendance
        ) in occurrence.onetimeeventparticipantattendance_set.all():
            if participant_attendance in self.cleaned_data["participants"]:
                participant_attendance.state = OneTimeEventAttendance.PRESENT
            else:
                participant_attendance.state = OneTimeEventAttendance.MISSING
            if commit:
                participant_attendance.save()

    def _update_organizers_attendance_transaction(self, commit, instance):
        for organizer_assignment in instance.organizeroccurrenceassignment_set.all():
            if organizer_assignment in self.cleaned_data["organizers"]:
                organizer_assignment.state = OneTimeEventAttendance.PRESENT
                organizer_amounts = self.cleaned_data["organizer_amounts"]
                if organizer_assignment.id not in organizer_amounts:
                    amount = organizer_assignment.transaction.amount
                else:
                    amount = organizer_amounts[organizer_assignment.id]
                if amount > 0:
                    if organizer_assignment.transaction is None:
                        organizer_assignment.transaction = Transaction(
                            amount=amount,
                            reason=f"Organizátor {instance.event} dne {instance.date}",
                            date_due=instance.date + timedelta(days=14),
                            person=organizer_assignment.person,
                            event=instance.event,
                        )
                    elif not organizer_assignment.transaction.is_settled:
                        organizer_assignment.transaction.amount = amount
                    if commit:
                        organizer_assignment.transaction.save()
            else:
                organizer_assignment.state = OneTimeEventAttendance.MISSING
                if (
                    organizer_assignment.transaction is not None
                    and not organizer_assignment.transaction.is_settled
                ):
                    organizer_assignment.transaction.delete()
                    organizer_assignment.transaction = None
            if commit:
                organizer_assignment.save()

    def checked_participant_assignments(self):
        if hasattr(self, "cleaned_data") and "participants" in self.cleaned_data:
            return self.cleaned_data["participants"]
        return OneTimeEventParticipantAttendance.objects.filter(
            Q(occurrence=self.instance), state=OneTimeEventAttendance.PRESENT
        )

    def checked_organizer_assignments(self):
        if hasattr(self, "cleaned_data") and "organizers" in self.cleaned_data:
            return self.cleaned_data["organizers"]
        return OrganizerOccurrenceAssignment.objects.filter(
            occurrence=self.instance, state=OneTimeEventAttendance.PRESENT
        )

    def organizer_amounts(self):
        if hasattr(self, "cleaned_data") and "organizer_amounts" in self.cleaned_data:
            return self.cleaned_data["organizer_amounts"]
        organizer_amounts = {}
        for (
            organizer_assignment
        ) in self.instance.organizeroccurrenceassignment_set.all():
            organizer_amounts[
                organizer_assignment.id
            ] = organizer_assignment.receive_amount()
        return organizer_amounts


class ReopenOneTimeEventOccurrenceForm(ModelForm):
    class Meta:
        model = OneTimeEventOccurrence
        fields = []

    def save(self, commit=True):
        instance = super().save(False)
        instance.state = EventOrOccurrenceState.OPEN
        instance.event.state = EventOrOccurrenceState.OPEN

        observed_assignments = [
            OneTimeEventParticipantAttendance.objects.filter(
                occurrence=instance, state=OneTimeEventAttendance.MISSING
            ),
            OrganizerOccurrenceAssignment.objects.filter(
                occurrence=instance, state=OneTimeEventAttendance.MISSING
            ),
        ]

        for assignments in observed_assignments:
            for assignment in assignments:
                assignment.state = OneTimeEventAttendance.PRESENT
                if commit:
                    assignment.save()

        if commit:
            instance.save()
            instance.event.save()
        return instance


class CancelOccurrenceApprovementForm(ReopenOccurrenceMixin, ModelForm):
    class Meta:
        model = OneTimeEventOccurrence
        fields = []

    def save(self, commit=True):
        instance = super().save(False)
        instance.state = EventOrOccurrenceState.OPEN
        instance.event.state = EventOrOccurrenceState.OPEN

        self._remove_organizer_attendance_transactions(commit, instance)
        self._remove_participant_attendance(commit, instance)

        if commit:
            instance.save()
            instance.event.save()
        return instance

    def _remove_organizer_attendance_transactions(self, commit, occurrence):
        organizer_assignments = OrganizerOccurrenceAssignment.objects.filter(
            occurrence=occurrence
        )
        for organizer_assignment in organizer_assignments:
            organizer_assignment.state = OneTimeEventAttendance.PRESENT
            if organizer_assignment.transaction is not None:
                organizer_assignment.transaction.delete()
                organizer_assignment.transaction = None
            if commit:
                organizer_assignment.save()

    def _remove_participant_attendance(self, commit, occurrence):
        participant_assignments = OneTimeEventParticipantAttendance.objects.filter(
            occurrence=occurrence
        )
        for participant_assignment in participant_assignments:
            participant_assignment.state = OneTimeEventAttendance.PRESENT
            if commit:
                participant_assignment.save()


class OneTimeEventCreateDuplicateForm(ModelForm):
    class Meta:
        model = OneTimeEvent
        fields = []
