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
from vzs.widgets import DatePickerWithIcon
from .models import Person, FeatureAssignment, Feature, StaticGroup, Transaction


class PersonForm(ModelForm):
    class Meta:
        model = Person
        exclude = ["features", "managed_persons"]
        widgets = {"date_of_birth": DatePickerWithIcon()}

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
    fee = forms.IntegerField(label=_("Poplatek"), required=False, min_value=0)
    due_date = forms.DateField(
        label=_("Datum splatnosti poplatku"),
        required=False,
        initial=datetime.date.today() + settings.VZS_DEFAULT_DUE_DATE,
        widget=widgets.DateInput(
            format=settings.DATE_INPUT_FORMATS, attrs={"type": "date"}
        ),
    )

    class Meta:
        model = FeatureAssignment
        fields = ["feature", "date_assigned", "date_expire", "issuer", "code"]
        widgets = {
            "date_assigned": DatePickerWithIcon(),
            "date_expire": DatePickerWithIcon(),
        }

    def __init__(self, *args, **kwargs):
        feature_type = kwargs.pop("feature_type", None)
        super().__init__(*args, **kwargs)
        if feature_type:
            self.fields["feature"].queryset = Feature.objects.filter(
                feature_type=feature_type, assignable=True
            )

        self._remove_not_collected_field()
        self._remove_non_valid_fields_by_type(feature_type)
        self._setup_fee_field()

    def _remove_not_collected_field(self):
        if self.instance.pk is None:
            return
        else:
            feature = self.instance.feature

        self.fields.pop("feature")

        if feature.never_expires is True:
            self.fields.pop("date_expire")

        if feature.collect_issuers is False:
            self.fields.pop("issuer")

        if feature.collect_codes is False:
            self.fields.pop("code")

        if not feature.fee:
            self.fields.pop("fee")
            self.fields.pop("due_date")

    def _remove_non_valid_fields_by_type(self, feature_type):
        non_valid_fields_for_feature_type = {
            Feature.Type.QUALIFICATION: ["fee", "due_date"],
            Feature.Type.PERMISSION: ["issuer", "code", "fee", "due_date"],
            Feature.Type.EQUIPMENT: ["issuer"],
        }

        for type, fields in non_valid_fields_for_feature_type.items():
            if feature_type == type:
                for field in fields:
                    self.fields.pop(field)

    def _setup_fee_field(self):
        if not self.instance or not hasattr(self.instance, "transaction"):
            return

        self.fields["fee"].initial = -self.instance.transaction.amount
        self.fields["due_date"].initial = self.instance.transaction.date_due

        if self.instance.transaction.is_settled():
            self.fields["fee"].disabled = True
            self.fields["due_date"].disabled = True

    def _get_feature(self, cleaned_data):
        if self.instance.pk is not None:
            return FeatureAssignment.objects.get(pk=self.instance.pk).feature
        else:
            return cleaned_data["feature"]

    def clean_fee(self):
        fee_value = self.cleaned_data.get("fee")
        feature_value = self._get_feature(self.cleaned_data)

        if not feature_value.fee and fee_value:
            raise ValidationError(
                _("Je vyplněn poplatek u vlastnosti, která nemá poplatek.")
            )

        if fee_value and feature_value.feature_type != Feature.Type.EQUIPMENT:
            raise ValidationError(
                _("Poplatek může být vyplněn pouze u vlastnosti typu vybavení.")
            )

        if (
            fee_value
            and self.instance
            and hasattr(self.instance, "transaction")
            and self.instance.transaction.is_settled()
            and -fee_value != self.instance.transaction.amount
        ):
            raise ValidationError(_("Poplatek nelze změnit, protože je již uhrazen."))

        return fee_value

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        feature_value = self._get_feature(self.cleaned_data)

        if due_date and feature_value.feature_type != Feature.Type.EQUIPMENT:
            raise ValidationError(
                _("Poplatek může být vyplněn pouze u vlastnosti typu vybavení.")
            )

        if (
            due_date
            and self.instance
            and hasattr(self.instance, "transaction")
            and self.instance.transaction.is_settled()
            and due_date != self.instance.transaction.date_due
        ):
            raise ValidationError(
                _("Datum splatnosti nelze změnit, protože poplatek je již uhrazen.")
            )

        return due_date

    def clean_date_expire(self):
        date_expire_value = self.cleaned_data["date_expire"]
        feature_value = self._get_feature(self.cleaned_data)

        if feature_value.never_expires and date_expire_value is not None:
            raise ValidationError(
                _("Je vyplněné datum expirace u vlastnosti s neomezenou platností.")
            )

        return date_expire_value

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

    def clean(self):
        cleaned_data = super().clean()
        date_expire_value = cleaned_data.get("date_expire")
        date_assigned_value = cleaned_data.get("date_assigned")
        fee = cleaned_data.get("fee")
        due_date = cleaned_data.get("due_date")

        if (
            date_expire_value
            and date_assigned_value
            and date_assigned_value > date_expire_value
        ):
            self.add_error(
                "date_expire", _("Datum expirace je nižší než datum přiřazení.")
            )

        if fee and not due_date:
            self.add_error(
                "due_date", _("Datum splatnosti poplatku musí být vyplněno.")
            )
        elif not fee and due_date:
            self.cleaned_data["due_date"] = None

    def add_transaction_if_necessary(self):
        fee = self.cleaned_data.get("fee")
        if fee is None or (
            hasattr(self.instance, "transaction")
            and self.instance.transaction.is_settled()
        ):
            return False

        feature = self._get_feature(self.cleaned_data)
        date_due = self.cleaned_data.get("due_date")

        transaction_data = {
            "amount": -fee,
            "reason": _(f"Poplatek za zapůjčení vybavení - {feature.name}"),
            "date_due": date_due,
        }

        if fee == 0:
            self.instance.transaction.delete()
        elif hasattr(self.instance, "transaction"):
            self.instance.transaction.__dict__.update(transaction_data)
            self.instance.transaction.save()
        else:
            transaction_data.update(
                {
                    "person": self.instance.person,
                    "feature_assigment": self.instance,
                }
            )
            Transaction.objects.create(**transaction_data)

        return True


class FeatureForm(ModelForm):
    class Meta:
        model = Feature
        fields = [
            "name",
            "parent",
            "assignable",
            "fee",
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
            self.fields.pop("fee")

        elif feature_type == Feature.Type.PERMISSION:
            self.fields.pop("fee")
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

    def clean_fee(self):
        fee = self.cleaned_data["fee"]

        if self.feature_type != Feature.Type.EQUIPMENT and fee is not None:
            raise ValidationError(
                _("Je vyplněn poplatek u jiných vlastností osob než jsou vybavení.")
            )

        if fee == 0:
            fee = None

        return fee

    def clean(self):
        assignable = self.cleaned_data["assignable"]
        fee = self.cleaned_data.get("fee")
        never_expires = self.cleaned_data.get("never_expires")
        collect_issuers = self.cleaned_data.get("collect_issuers")
        collect_codes = self.cleaned_data.get("collect_codes")

        if not assignable and (
            fee or never_expires or collect_issuers or collect_codes
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
        age_from = cleaned_data.get("age_from")
        age_to = cleaned_data.get("age_to")

        if age_from and age_to and age_from > age_to:
            raise ValidationError(_("Věk od musí být menší nebo roven věku do."))


class TransactionCreateEditBaseForm(ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount", "reason", "date_due"]
        widgets = {
            "date_due": DatePickerWithIcon(),
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

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        is_reward = cleaned_data.get("is_reward")

        if not is_reward:
            cleaned_data["amount"] = -amount

        return cleaned_data


class TransactionCreateForm(TransactionCreateEditBaseForm):
    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.person = person


class TransactionEditForm(TransactionCreateEditBaseForm):
    def __init__(self, instance, initial, *args, **kwargs):
        initial["is_reward"] = instance.amount > 0
        instance.amount = abs(instance.amount)

        super().__init__(instance=instance, initial=initial, *args, **kwargs)
