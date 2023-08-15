from django.forms import ModelForm
from django.forms import ChoiceField
from persons.models import Person, PersonType


class AgeLimitForm(ModelForm):
    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data["min_age"] is not None
            and cleaned_data["max_age"] is not None
            and cleaned_data["min_age"] > cleaned_data["max_age"]
        ):
            self.add_error(
                "max_age",
                "Hodnota minimálního věku musí být menší nebo rovna hodnotě maximálního věku",
            )
        return cleaned_data


class GroupMembershipForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].required = False


class AllowedPersonTypeForm(ModelForm):
    person_type = ChoiceField(required=True, choices=Person.Type.choices)

    def save(self, commit=True):
        person_type = self.cleaned_data["person_type"]
        person_type_obj, _ = PersonType.objects.get_or_create(
            person_type=person_type, defaults={"person_type": person_type}
        )
        if self.instance.allowed_person_types.contains(person_type_obj):
            self.instance.allowed_person_types.remove(person_type_obj)
        else:
            self.instance.allowed_person_types.add(person_type_obj)
        if commit:
            self.instance.save()
