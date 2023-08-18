from django.forms import ModelForm
from django.forms import ChoiceField
from persons.models import Person
from persons.widgets import PersonSelectWidget
from events.models import EventPersonTypeConstraint
from django_select2.forms import Select2Widget
from datetime import datetime
from events.models import ParticipantEnrollment


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
        labels = {"group": "Skupina"}
        widgets = {
            "group": Select2Widget(attrs={"onchange": "groupChanged(this)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].required = False


class AllowedPersonTypeForm(ModelForm):
    class Meta:
        fields = []

    person_type = ChoiceField(required=True, choices=Person.Type.choices)

    def save(self, commit=True):
        instance = super().save(False)
        person_type = self.cleaned_data["person_type"]
        person_type_obj = EventPersonTypeConstraint.get_or_create_person_type(
            person_type
        )
        if instance.allowed_person_types.contains(person_type_obj):
            instance.allowed_person_types.remove(person_type_obj)
        else:
            instance.allowed_person_types.add(person_type_obj)
        if commit:
            instance.save()
        return instance


class EventParticipantEnrollmentForm(ModelForm):
    class Meta:
        fields = ["person", "state"]
        labels = {"person": "Osoba"}
        widgets = {
            "person": PersonSelectWidget(attrs={"onchange": "personChanged(this)"}),
            "state": Select2Widget(attrs={"onchange": "stateChanged()"}),
        }

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event")
        self.person = kwargs.pop("person", None)
        super().__init__(*args, **kwargs)
        if self.instance.id is None:
            self.fields["person"].queryset = Person.objects.exclude(
                pk__in=self.event.enrolled_participants.all().values_list(
                    "pk", flat=True
                )
            )
        else:
            self.fields["person"].widget.attrs["disabled"] = True

    def save(self, commit=True):
        instance = super().save(False)
        instance.event = self.event

        if instance.id is not None:
            instance.person = self.person
        else:
            instance.datetime = datetime.now()

        if instance.state != ParticipantEnrollment.State.APPROVED:
            instance.agreed_participation_fee = None

        if commit:
            instance.save()
        return instance
