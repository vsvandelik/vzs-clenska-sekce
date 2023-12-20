from re import sub as regex_sub

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset, Layout, Submit
from django.forms import (
    CharField,
    ChoiceField,
    EmailField,
    Form,
    IntegerField,
    ModelChoiceField,
    ModelForm,
    ValidationError,
)
from django.utils.translation import gettext_lazy as _

from features.models import Feature
from one_time_events.models import OneTimeEvent
from trainings.models import Training
from vzs.forms import WithoutFormTagFormHelper
from vzs.mixin_extensions import (
    RelatedAddMixin,
    RelatedAddOrRemoveFormMixin,
    RelatedRemoveMixin,
)
from vzs.utils import today
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

        if date_of_birth is not None and date_of_birth > today():
            raise ValidationError(_("Neplatné datum narození."))

        return date_of_birth

    def clean_birth_number(self):
        birth_number = self.cleaned_data["birth_number"]

        persons_with_same_birth_number = Person.objects.filter(
            birth_number=birth_number
        ).exclude(pk=self.instance.pk)

        if birth_number is not None and persons_with_same_birth_number.exists():
            raise ValidationError(
                _(
                    "Rodné číslo je již použito. Zkontrolujte prosím,"
                    "jestli daná osoba již neexistuje."
                )
            )

        return birth_number

    def clean_phone(self):
        phone = self.cleaned_data["phone"]

        if phone is None:
            return None

        phone = regex_sub(r"\D", "", phone)  # remove non digits

        if phone.startswith("00420"):
            phone = phone[5:]
        elif phone.startswith("420"):
            phone = phone[3:]

        if len(phone) != 9:
            raise ValidationError(_("Telefonní číslo nemá platný formát."))

        return phone

    def clean_postcode(self):
        postcode = self.cleaned_data["postcode"]

        if postcode is None:
            return None

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


class AddDeleteManagedPersonFormMixin(RelatedAddOrRemoveFormMixin):
    class Meta:
        fields = []
        model = Person

    managed_person = ModelChoiceField(queryset=Person.objects.all())
    instance_to_add_or_remove_field_name = "managed_person"

    def _get_instances(self):
        return self.instance.managed_persons


class AddManagedPersonForm(RelatedAddMixin, AddDeleteManagedPersonFormMixin):
    error_message = _("Daný vztah spravované osoby je již zadán.")

    def clean_managed_person(self):
        managed_person = self.cleaned_data["managed_person"]

        if managed_person == self.instance:
            raise ValidationError(_("Osoba nemůže spravovat samu sebe."))

        return managed_person


class DeleteManagedPersonForm(RelatedRemoveMixin, AddDeleteManagedPersonFormMixin):
    error_message = _("Daný vztah spravované osoby neexistuje.")


class PersonsFilterForm(Form):
    name = CharField(label=_("Jméno"), required=False)
    email = EmailField(label=_("E-mailová adresa"), required=False)
    qualifications = ModelChoiceField(
        label=_("Kvalifikace"), required=False, queryset=Feature.qualifications.all()
    )
    permissions = ModelChoiceField(
        label=_("Oprávnění"), required=False, queryset=Feature.permissions.all()
    )
    equipments = ModelChoiceField(
        label=_("Vybavení"), required=False, queryset=Feature.equipments.all()
    )
    person_type = ChoiceField(
        label=_("Typ osoby"),
        required=False,
        choices=[("", "---------")] + Person.Type.choices,
    )
    age_from = IntegerField(label=_("Věk od"), required=False, min_value=1)
    age_to = IntegerField(label=_("Věk do"), required=False, min_value=1)

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


class PersonHourlyRateForm(Form):
    def __init__(self, *args, **kwargs):
        self.person_instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)

        for key, label in OneTimeEvent.Category.choices:
            self.fields[key] = IntegerField(
                label=label,
                required=False,
                min_value=0,
            )

        for key, label in Training.Category.choices:
            self.fields[key] = IntegerField(
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
