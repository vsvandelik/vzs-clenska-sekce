import datetime
import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div
from django import forms
from django.forms import ModelForm, widgets, ValidationError, Form
from django.utils.translation import gettext_lazy as _

from google_integration import google_directory
from vzs import settings
from vzs.forms import VZSDefaultFormHelper
from .models import Person, FeatureAssignment, Feature, StaticGroup, Transaction


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
        self.available_person_types = kwargs.pop("available_person_types", [])

        super().__init__(*args, **kwargs)

        self.helper = VZSDefaultFormHelper()
        self.helper.add_input(Submit("submit", "Uložit"))

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

            if self.instance.feature.collect_issuers is False:
                self.fields.pop("issuer")

            if self.instance.feature.collect_codes is False:
                self.fields.pop("code")

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
        fields = [
            "name",
            "parent",
            "assignable",
            "tier",
            "never_expires",
            "collect_issuers",
            "collect_codes",
        ]
        widgets = {
            "never_expires": widgets.CheckboxInput(),
            "collect_issuers": widgets.CheckboxInput(),
            "collect_codes": widgets.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        feature_type = kwargs.pop("feature_type", None)
        super().__init__(*args, **kwargs)
        if not feature_type:
            return

        self.fields["parent"].queryset = Feature.objects.filter(
            feature_type=feature_type
        )
        self.feature_type = feature_type

        if feature_type == Feature.Type.QUALIFICATION:
            self.fields.pop("tier")

        elif feature_type == Feature.Type.PERMISSION:
            self.fields.pop("tier")
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

    def clean_tier(self):
        tier = self.cleaned_data["tier"]

        if self.feature_type != Feature.Type.EQUIPMENT and tier is not None:
            raise ValidationError(
                _("Je vyplněn poplatek u jiných vlastností osob než jsou vybavení.")
            )

        return tier

    def clean(self):
        assignable = self.cleaned_data["assignable"]
        tier = self.cleaned_data.get("tier")
        never_expires = self.cleaned_data.get("never_expires")
        collect_issuers = self.cleaned_data.get("collect_issuers")
        collect_codes = self.cleaned_data.get("collect_codes")

        if not assignable and (
            tier or never_expires or collect_issuers or collect_codes
        ):
            raise ValidationError(
                _(
                    "Je vyplněna vlastnost, která se vztahuje pouze na přiřaditelné vlastnosti."
                )
            )
        elif not assignable:
            self.cleaned_data["never_expires"] = None
            self.cleaned_data["collect_issuers"] = None
            self.cleaned_data["collect_codes"] = None


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
    age_from = forms.IntegerField(label=_("Věk od"), required=False)
    age_to = forms.IntegerField(label=_("Věk do"), required=False)

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

    def clean_age_from(self):
        if self.cleaned_data["age_from"] and self.cleaned_data["age_from"] <= 0:
            raise ValidationError(_("Věk musí být kladné celé číslo."))

        return self.cleaned_data["age_from"]

    def clean_age_to(self):
        if self.cleaned_data["age_to"] and self.cleaned_data["age_to"] <= 0:
            raise ValidationError(_("Věk musí být kladné celé číslo."))

        return self.cleaned_data["age_to"]

    def clean(self):
        cleaned_data = super().clean()
        age_from = cleaned_data.get("age_from")
        age_to = cleaned_data.get("age_to")

        if age_from and age_to and age_from > age_to:
            raise ValidationError(_("Věk od musí být menší nebo roven věku do."))


class TransactionCreateEditBaseForm(ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount", "reason", "date_due"]
        widgets = {
            "date_due": widgets.DateInput(
                format=settings.DATE_INPUT_FORMATS, attrs={"type": "date"}
            ),
        }

    amount = forms.IntegerField(
        min_value=1, label=Transaction._meta.get_field("amount").verbose_name
    )
    is_reward = forms.BooleanField(required=False, label=_("Je transakce odměna?"))

    def clean_date_due(self):
        date_due = self.cleaned_data["date_due"]

        if date_due < datetime.date.today():
            raise ValidationError(_("Datum splatnosti nemůže být v minulosti."))

        return date_due

    def save(self, commit=True):
        transaction = super().save(False)

        if not self.cleaned_data["is_reward"]:
            transaction.amount *= -1

        if commit:
            transaction.save()

        return transaction


class TransactionCreateForm(TransactionCreateEditBaseForm):
    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.person = person

    def save(self, commit=True):
        transaction = super().save(False)

        transaction.person = self.person

        if commit:
            transaction.save()

        return transaction


class TransactionEditForm(TransactionCreateEditBaseForm):
    def __init__(self, instance, initial, *args, **kwargs):
        if instance.amount > 0:
            if "is_reward" not in initial:
                initial["is_reward"] = True

        instance.amount = abs(instance.amount)
        super().__init__(instance=instance, initial=initial, *args, **kwargs)
