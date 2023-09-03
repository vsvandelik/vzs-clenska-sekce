from datetime import datetime

from django.db.models import Q
from django.forms import ChoiceField
from django.forms import ModelForm
from django.utils import timezone
from django_select2.forms import Select2Widget

from events.models import (
    EventPersonTypeConstraint,
    ParticipantEnrollment,
    OrganizerAssignment,
)
from persons.models import Person
from persons.widgets import PersonSelectWidget
from vzs.widgets import DatePickerWithIcon


class EventForm(ModelForm):
    class Meta:
        fields = [
            "name",
            "category",
            "description",
            "capacity",
            "location",
            "date_start",
            "date_end",
            "participants_enroll_state",
        ]
        widgets = {
            "category": Select2Widget(),
            "date_start": DatePickerWithIcon(attrs={"onchange": "dateChanged()"}),
            "date_end": DatePickerWithIcon(attrs={"onchange": "dateChanged()"}),
            "participants_enroll_state": Select2Widget(),
        }


class AgeLimitForm(ModelForm):
    class Meta:
        fields = ["min_age", "max_age"]

    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get("min_age")
        max_age = cleaned_data.get("max_age")

        if min_age is not None and max_age is not None and min_age > max_age:
            self.add_error(
                "max_age",
                "Hodnota minimálního věku musí být menší nebo rovna hodnotě maximálního věku",
            )
        return cleaned_data


class GroupMembershipForm(ModelForm):
    class Meta:
        fields = ["group"]
        widgets = {
            "group": Select2Widget(attrs={"onchange": "groupChanged(this)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].required = False


class AllowedPersonTypeForm(ModelForm):
    class Meta:
        fields = []

    person_type = ChoiceField(choices=Person.Type.choices)

    def save(self, commit=True):
        instance = super().save(False)
        person_type = self.cleaned_data["person_type"]
        person_type_obj = EventPersonTypeConstraint.get_or_create(person_type)
        if instance.allowed_person_types.contains(person_type_obj):
            instance.allowed_person_types.remove(person_type_obj)
        else:
            instance.allowed_person_types.add(person_type_obj)
        if commit:
            instance.save()
        return instance


class ParticipantEnrollmentForm(ModelForm):
    class Meta:
        fields = ["person", "state"]
        widgets = {
            "person": PersonSelectWidget(attrs={"onchange": "personChanged(this)"}),
            "state": Select2Widget(attrs={"onchange": "stateChanged()"}),
        }

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event")
        self.person = kwargs.pop("person", None)
        super().__init__(*args, **kwargs)
        if self.instance.id is None:
            if self.event.is_one_time_event():
                persons_not_attending_query = ~Q(
                    onetimeeventparticipantenrollment__one_time_event=self.event
                )
            elif self.event.is_training():
                persons_not_attending_query = ~Q(
                    trainingparticipantenrollment__training=self.event
                )
            else:
                raise NotImplementedError

            self.fields["person"].queryset = Person.objects.filter(
                persons_not_attending_query
            )
        else:
            self.fields["person"].widget.attrs["disabled"] = True

    def save(self, commit=True):
        instance = super().save(False)
        instance.event = self.event

        if instance.id is not None:
            instance.person = self.person
        else:
            instance.created_datetime = datetime.now(tz=timezone.get_default_timezone())

        if commit:
            instance.save()
        return instance


class EnrollMyselfForm(ModelForm):
    class Meta:
        fields = []

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop("request").active_person
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.person is None:
            self.add_error(None, "Není přihlášena žádná osoba")
        return cleaned_data


class EnrollMyselfParticipantForm(EnrollMyselfForm):
    class Meta(EnrollMyselfForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if (
            self.person is not None
            and not self.event.does_participant_satisfy_requirements(self.person)
        ):
            self.add_error(
                None,
                f"Nejsou splněny požadavky kladené na účastníky události",
            )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(False)
        instance.created_datetime = datetime.now(tz=timezone.get_default_timezone())
        instance.person = self.person

        if commit:
            instance.save()
        return instance


class OrganizerAssignmentForm(ModelForm):
    class Meta:
        fields = ["position_assignment", "person"]
        widgets = {
            "person": PersonSelectWidget(attrs={"onchange": "personChanged(this)"}),
            "position_assignment": Select2Widget(),
        }


class BulkApproveParticipantsForm(ModelForm):
    class Meta:
        fields = []
