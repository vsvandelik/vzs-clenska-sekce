import datetime
import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, Reset
from django import forms
from django.forms import ModelForm, widgets, ValidationError, Form
from django.utils.translation import gettext_lazy as _

from google_integration import google_directory
from vzs import settings
from vzs.forms import VZSDefaultFormHelper
from .models import Person, FeatureAssignment, Feature, StaticGroup


class PersonForm(ModelForm):
    class Meta:
        model = Person
        exclude = ["features", "managed_persons"]
        widgets = {
            "date_of_birth": widgets.DateInput(
                format=settings.DATE_INPUT_FORMATS, attrs={"type": "date"}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = VZSDefaultFormHelper()
        self.helper.add_input(Submit("submit", "Uložit"))

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


class FeatureAssignmentForm(ModelForm):
    class Meta:
        model = FeatureAssignment
        fields = ["feature", "date_assigned", "date_expire", "issuer", "code"]
        widgets = {
            "date_assigned": widgets.DateInput(
                format=settings.DATE_INPUT_FORMATS, attrs={"type": "date"}
            ),
            "date_expire": widgets.DateInput(
                format=settings.DATE_INPUT_FORMATS, attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        feature_type = kwargs.pop("feature_type", None)
        super().__init__(*args, **kwargs)
        if feature_type:
            self.fields["feature"].queryset = Feature.objects.filter(
                feature_type=feature_type, assignable=True
            )

        if self.instance.pk is not None:
            self.fields.pop("feature")

            if self.instance.feature.never_expires is True:
                self.fields.pop("date_expire")

        if feature_type == Feature.Type.PERMISSION:
            self.fields.pop("issuer")
            self.fields.pop("code")

        elif feature_type == Feature.Type.EQUIPMENT:
            self.fields.pop("issuer")

    def _get_feature(self, cleaned_data):
        if self.instance.pk is not None:
            return FeatureAssignment.objects.get(pk=self.instance.pk).feature
        else:
            return cleaned_data["feature"]

    def clean_date_expire(self):
        date_expire_value = self.cleaned_data["date_expire"]
        feature_value = self._get_feature(self.cleaned_data)

        if feature_value.never_expires and date_expire_value is not None:
            raise ValidationError(
                _("Je vyplněné datum expirace u vlastnosti s neomezenou platností.")
            )

        return date_expire_value

    def clean(self):
        cleaned_data = super().clean()
        date_expire_value = cleaned_data.get("date_expire")
        date_assigned_value = cleaned_data.get("date_assigned")

        if (
            date_expire_value
            and date_assigned_value
            and date_assigned_value > date_expire_value
        ):
            self.add_error(
                "date_expire", _("Datum expirace je nižší než datum přiřazení.")
            )

    def clean_issuer(self):
        issuer = self.cleaned_data["issuer"]
        feature = self._get_feature(self.cleaned_data)

        if not feature.collect_issuers and issuer is not None:
            raise ValidationError(
                _("Je vyplněn vydavatel u vlastnosti u které se vydavatel neeviduje.")
            )

        return issuer

    def clean_code(self):
        code = self.cleaned_data["code"]
        feature = self._get_feature(self.cleaned_data)

        if not feature.collect_codes and code is not None:
            raise ValidationError(
                _(
                    "Je vyplněn kód vlastnosti u vlastnosti u které se vydavatel neeviduje."
                )
            )

        return code


class FeatureForm(ModelForm):
    class Meta:
        model = Feature
        fields = "__all__"
        exclude = ["feature_type"]

    def __init__(self, *args, **kwargs):
        feature_type = kwargs.pop("feature_type", None)
        super().__init__(*args, **kwargs)
        if feature_type:
            self.fields["parent"].queryset = Feature.objects.filter(
                feature_type=feature_type
            )
            self.feature_type = feature_type

        if feature_type == Feature.Type.PERMISSION:
            self.fields.pop("collect_issuers")
            self.fields.pop("collect_codes")

        elif feature_type == Feature.Type.EQUIPMENT:
            self.fields.pop("collect_issuers")

    def clean_collect_issuers(self):
        collect_issuers = self.cleaned_data["collect_issuers"]

        if self.feature_type != Feature.Type.QUALIFICATION and collect_issuers:
            raise ValidationError(
                _(
                    "Je vyplněno zadávání vydavatelů u jiných vlastností osob než jsou kvalifikace."
                )
            )

        return collect_issuers

    def clean_collect_codes(self):
        collect_codes = self.cleaned_data["collect_codes"]

        if self.feature_type == Feature.Type.PERMISSION and collect_codes:
            raise ValidationError(_("Je vyplněno zadávání kódů u oprávnění."))

        return collect_codes


class StaticGroupForm(ModelForm):
    class Meta:
        model = StaticGroup
        exclude = ["members"]

    def clean_google_email(self):
        all_groups = google_directory.get_list_of_groups()

        emails_of_groups = [group["email"] for group in all_groups]

        if (
            self.cleaned_data["google_email"]
            and self.cleaned_data["google_email"] not in emails_of_groups
        ):
            raise ValidationError(
                _("E-mailová adresa Google skupiny neodpovídá žádné reálné skupině.")
            )

        return self.cleaned_data["google_email"]

    def clean(self):
        cleaned_data = super().clean()
        google_as_members_authority = cleaned_data.get("google_as_members_authority")
        google_email = cleaned_data.get("google_email")

        if google_as_members_authority and not google_email:
            raise ValidationError(
                _(
                    "Google nemůže být jako autorita členů skupiny v situaci, kdy není vyplněna emailová adresa skupiny."
                )
            )


class AddMembersStaticGroupForm(ModelForm):
    class Meta:
        model = StaticGroup
        fields = ["members"]


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
    email = forms.CharField(label=_("E-mailová adresa"), required=False)
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
    birth_year_from = forms.IntegerField(label=_("Rok narození od"), required=False)
    birth_year_to = forms.IntegerField(label=_("Rok narození do"), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "GET"
        self.helper.layout = Layout(
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
                Div("birth_year_from", css_class="col-md-3"),
                Div("birth_year_to", css_class="col-md-3"),
                css_class="row",
            ),
            Submit("submit", "Filtrovat", css_class="btn btn-primary float-right"),
        )
