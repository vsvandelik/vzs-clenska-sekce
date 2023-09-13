import datetime
import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, Fieldset
from django import forms
from django.forms import ModelForm, ValidationError, Form
from django.utils.translation import gettext_lazy as _

from features.models import Feature
from one_time_events.models import OneTimeEvent
from trainings.models import Training
from vzs.forms import WithoutFormTagFormHelper
from vzs.widgets import DatePickerWithIcon
from .models import Person, PersonHourlyRate


class PersonForm(ModelForm):
    class Meta:
        model = Person
        exclude = ["features", "managed_persons"]
        widgets = {"date_of_birth": DatePickerWithIcon()}

    def __init__(self, *args, **kwargs):
        self.available_person_types = kwargs.pop("available_person_types", [])

        super().__init__(*args, **kwargs)

        self.helper = WithoutFormTagFormHelper()

        if "person_type" in self.fields:
            self.fields["person_type"].choices = [("", "---------")] + [
                (pt, pt.label) for pt in self.available_person_types
            ]

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data["date_of_birth"]

        if date_of_birth and date_of_birth > datetime.date.today():
            raise ValidationError(_("Neplatné datum narození."))

        return date_of_birth

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if not phone:
            return phone

        phone = re.sub(r"\D", "", phone)  # remove non digits

        if phone.startswith("00420"):
            phone = phone[5:]
        elif phone.startswith("420"):
            phone = phone[3:]

        if len(phone) != 9:
            raise ValidationError(_("Telefonní číslo nemá platný formát."))

        return phone

    def clean_postcode(self):
        postcode = self.cleaned_data["postcode"]
        if not postcode:
            return postcode

        if len(str(postcode)) != 5:
            raise ValidationError(_("PSČ nemá platný formát."))

        return postcode


class MyProfileUpdateForm(PersonForm):
    class Meta:
        model = Person
        fields = [
            "email",
            "phone",
            "health_insurance_company",
            "street",
            "city",
            "postcode",
        ]


class AddDeleteManagedPersonForm(Form):
    person = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        self.managing_person = kwargs.pop("managing_person", None)
        super().__init__(*args, **kwargs)

    def clean_person(self):
        managed_person_pk = self.cleaned_data.get("person")

        try:
            managing_person_instance = Person.objects.get(pk=self.managing_person)
            self.cleaned_data["managing_person_instance"] = managing_person_instance
        except Person.DoesNotExist:
            raise forms.ValidationError(_("Daná osoba neexistuje."))

        try:
            managed_person_instance = Person.objects.get(pk=managed_person_pk)
            self.cleaned_data["managed_person_instance"] = managed_person_instance
        except Person.DoesNotExist:
            raise forms.ValidationError(_("Daná osoba neexistuje."))

        if (
            managed_person_pk
            and self.managing_person
            and managed_person_pk == self.managing_person
        ):
            raise forms.ValidationError(_("Osoba nemůže spravovat samu sebe."))

        return managed_person_pk


class AddManagedPersonForm(AddDeleteManagedPersonForm):
    def clean_person(self):
        result = super().clean_person()

        if self.cleaned_data["managing_person_instance"].managed_persons.contains(
            self.cleaned_data["managed_person_instance"]
        ):
            raise forms.ValidationError(_("Daný vztah spravované osoby je již zadán."))

        return result


class DeleteManagedPersonForm(AddDeleteManagedPersonForm):
    pass


class PersonsFilterForm(forms.Form):
    name = forms.CharField(label=_("Jméno"), required=False)
    email = forms.EmailField(label=_("E-mailová adresa"), required=False)
    qualifications = forms.ModelChoiceField(
        label=_("Kvalifikace"), required=False, queryset=Feature.qualifications.all()
    )
    permissions = forms.ModelChoiceField(
        label=_("Oprávnění"), required=False, queryset=Feature.permissions.all()
    )
    equipments = forms.ModelChoiceField(
        label=_("Vybavení"), required=False, queryset=Feature.equipments.all()
    )
    person_type = forms.ChoiceField(
        label=_("Typ osoby"),
        required=False,
        choices=[("", "---------")] + Person.Type.choices,
    )
    age_from = forms.IntegerField(label=_("Věk od"), required=False, min_value=1)
    age_to = forms.IntegerField(label=_("Věk do"), required=False, min_value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "GET"
        self.helper.form_id = "persons-filter-form"
        self.helper.layout = Layout(
            Div(
                Div(
                    Div("name", css_class="col-md-6"),
                    Div("email", css_class="col-md-6"),
                    css_class="row",
                ),
                Div(
                    Div("qualifications", css_class="col-md-4"),
                    Div("permissions", css_class="col-md-4"),
                    Div("equipments", css_class="col-md-4"),
                    css_class="row",
                ),
                Div(
                    Div("person_type", css_class="col-md-6"),
                    Div("age_from", css_class="col-md-3"),
                    Div("age_to", css_class="col-md-3"),
                    css_class="row",
                ),
                Div(
                    Div(
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

    def clean(self):
        cleaned_data = super().clean()
        return self.clean_with_given_values(cleaned_data)

    @staticmethod
    def clean_with_given_values(cleaned_data):
        age_from = cleaned_data.get("age_from")
        age_to = cleaned_data.get("age_to")

        if age_from and age_to and age_from > age_to:
            raise ValidationError(_("Věk od musí být menší nebo roven věku do."))

        return cleaned_data


class PersonHourlyRateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.person_instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)

        for key, label in OneTimeEvent.Category.choices:
            self.fields[key] = forms.IntegerField(
                label=label,
                required=False,
                min_value=0,
            )

        for key, label in Training.Category.choices:
            self.fields[key] = forms.IntegerField(
                label=label,
                required=False,
                min_value=0,
            )

        self.initial = PersonHourlyRate.get_person_hourly_rates(self.person_instance)

        self.helper = WithoutFormTagFormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "Jednorázové akce", *[key for key, _ in OneTimeEvent.Category.choices]
            ),
            Fieldset("Tréninky", *[key for key, _ in Training.Category.choices]),
        )

    def save(self):
        cleaned_data = self.cleaned_data

        stored_hourly_rates = PersonHourlyRate.get_person_hourly_rates(
            self.person_instance
        )

        for event_type, hourly_rate in cleaned_data.items():
            stored_rate = stored_hourly_rates.get(event_type)

            if hourly_rate:
                if stored_rate is None:
                    PersonHourlyRate.objects.create(
                        person=self.person_instance,
                        event_type=event_type,
                        hourly_rate=hourly_rate,
                    )
                elif stored_rate != hourly_rate:
                    PersonHourlyRate.objects.filter(
                        person=self.person_instance, event_type=event_type
                    ).update(hourly_rate=hourly_rate)
            elif stored_rate is not None:
                PersonHourlyRate.objects.filter(
                    person=self.person_instance, event_type=event_type
                ).delete()

        types_to_remove = set(stored_hourly_rates.keys()) - set(cleaned_data.keys())
        PersonHourlyRate.objects.filter(
            person=self.person_instance, event_type__in=types_to_remove
        ).delete()

        return self.person_instance.hourly_rates
