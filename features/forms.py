from django.forms import DateField, IntegerField, ModelForm, ValidationError, widgets
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _

from persons.models import Person
from persons.widgets import PersonSelectWidget
from transactions.models import Transaction
from vzs.forms import WithoutFormTagMixin
from vzs.settings import VZS_DEFAULT_DUE_DATE
from vzs.utils import today
from vzs.widgets import DatePickerWithIcon

from .models import Feature, FeatureAssignment


class FeatureAssignmentBaseFormMixin(ModelForm):
    fee = IntegerField(label=_("Poplatek"), required=False, min_value=0)
    due_date = DateField(
        label=_("Datum splatnosti poplatku"),
        required=False,
        initial=today() + VZS_DEFAULT_DUE_DATE,
        widget=DatePickerWithIcon(),
    )

    class Meta:
        fields = ["date_assigned", "date_expire", "date_returned", "issuer", "code"]
        model = FeatureAssignment
        widgets = {
            "date_assigned": DatePickerWithIcon(),
            "date_expire": DatePickerWithIcon(),
            "date_returned": DatePickerWithIcon(),
        }

    def _remove_not_collected_field(self, feature):
        if "feature" in self.fields:
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
            Feature.Type.QUALIFICATION: ["fee", "due_date", "date_returned"],
            Feature.Type.PERMISSION: [
                "issuer",
                "code",
                "fee",
                "due_date",
                "date_returned",
            ],
            Feature.Type.EQUIPMENT: ["issuer"],
        }

        for type, fields in non_valid_fields_for_feature_type.items():
            if feature_type == type:
                for field in fields:
                    if field in self.fields:
                        self.fields.pop(field)

    def _setup_fee_field(self):
        if not self.instance or not hasattr(self.instance, "transaction"):
            return

        self.fields["fee"].initial = -self.instance.transaction.amount
        self.fields["due_date"].initial = self.instance.transaction.date_due

        if self.instance.transaction.is_settled:
            self.fields["fee"].disabled = True
            self.fields["due_date"].disabled = True

    def _get_feature(self, cleaned_data):
        if hasattr(self.instance, "feature"):
            return self.instance.feature
        elif self.instance.pk is not None:
            return FeatureAssignment.objects.get(pk=self.instance.pk).feature
        elif "feature" in cleaned_data:
            return cleaned_data["feature"]
        else:
            return None

    def clean_feature(self):
        feature = self.cleaned_data.get("feature")

        if feature is None:
            raise ValidationError(_("Položka k přiřazení není správně vyplněna."))

        return feature

    def clean_fee(self):
        fee_value = self.cleaned_data.get("fee")
        feature_value = self._get_feature(self.cleaned_data)

        if not feature_value:
            return fee_value

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
            and self.instance.transaction.is_settled
            and -fee_value != self.instance.transaction.amount
        ):
            raise ValidationError(_("Poplatek nelze změnit, protože je již uhrazen."))

        return fee_value

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        feature_value = self._get_feature(self.cleaned_data)

        if not feature_value:
            return due_date

        if due_date and feature_value.feature_type != Feature.Type.EQUIPMENT:
            raise ValidationError(
                _("Poplatek může být vyplněn pouze u vlastnosti typu vybavení.")
            )

        if (
            due_date
            and self.instance
            and hasattr(self.instance, "transaction")
            and self.instance.transaction.is_settled
            and due_date != self.instance.transaction.date_due
        ):
            raise ValidationError(
                _("Datum splatnosti nelze změnit, protože poplatek je již uhrazen.")
            )

        return due_date

    def clean_date_expire(self):
        date_expire_value = self.cleaned_data["date_expire"]
        feature_value = self._get_feature(self.cleaned_data)

        if not feature_value:
            return date_expire_value

        if feature_value.never_expires and date_expire_value is not None:
            raise ValidationError(
                _("Je vyplněné datum expirace u vlastnosti s neomezenou platností.")
            )

        return date_expire_value

    def clean_date_returned(self):
        date_returned = self.cleaned_data.get("date_returned")
        feature_value = self._get_feature(self.cleaned_data)

        if date_returned and feature_value.feature_type != Feature.Type.EQUIPMENT:
            raise ValidationError(
                _("Datum vrácení může být vyplněno pouze u vlastnosti typu vybavení.")
            )

        if date_returned and date_returned > today():
            raise ValidationError(_("Datum vrácení nemůže být v budoucnosti."))

        return date_returned

    def clean_issuer(self):
        issuer = self.cleaned_data["issuer"]
        feature = self._get_feature(self.cleaned_data)

        if not feature:
            return issuer

        if not feature.collect_issuers and issuer is not None:
            raise ValidationError(
                _("Je vyplněn vydavatel u vlastnosti u které se vydavatel neeviduje.")
            )

        return issuer

    def clean_code(self):
        code = self.cleaned_data["code"]
        feature = self._get_feature(self.cleaned_data)

        if not feature:
            return code

        if not feature.collect_codes and code is not None:
            raise ValidationError(
                _(
                    "Je vyplněn kód vlastnosti u vlastnosti u které se vydavatel neeviduje."
                )
            )

        return code

    def clean(self):
        cleaned_data = super().clean()
        date_expire = cleaned_data.get("date_expire")
        date_assigned = cleaned_data.get("date_assigned")
        date_returned = cleaned_data.get("date_returned")
        fee = cleaned_data.get("fee")
        due_date = cleaned_data.get("due_date")

        if date_expire and date_assigned and date_assigned > date_expire:
            self.add_error(
                "date_expire", _("Datum expirace je nižší než datum přiřazení.")
            )

        if fee and not due_date:
            self.add_error(
                "due_date", _("Datum splatnosti poplatku musí být vyplněno.")
            )
        elif not fee and due_date:
            self.cleaned_data["due_date"] = None

        if date_assigned and date_returned and date_returned < date_assigned:
            self.add_error(
                "date_returned",
                _("Datum vrácení nemůže být nižší než datum zapůjčení."),
            )

    def add_transaction_if_necessary(self):
        fee = self.cleaned_data.get("fee")
        if fee is None or (
            hasattr(self.instance, "transaction")
            and self.instance.transaction.is_settled
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


class FeatureAssignmentByPersonForm(
    WithoutFormTagMixin, FeatureAssignmentBaseFormMixin
):
    class Meta(FeatureAssignmentBaseFormMixin.Meta):
        fields = ["feature"] + FeatureAssignmentBaseFormMixin.Meta.fields
        widgets = FeatureAssignmentBaseFormMixin.Meta.widgets
        widgets["person"] = PersonSelectWidget()

    def __init__(self, feature_type, person, *args, **kwargs):
        super().__init__(*args, **kwargs)

        queryset = Feature.objects.filter(feature_type=feature_type, assignable=True)
        if feature_type == Feature.Type.PERMISSION:
            queryset = queryset.exclude(featureassignment__person=person)

        self.fields["feature"].queryset = queryset

        if self.instance.pk:
            self._remove_not_collected_field(self.instance.feature)

        self._remove_non_valid_fields_by_type(feature_type)
        self._setup_fee_field()


class FeatureAssignmentByFeatureForm(
    WithoutFormTagMixin, FeatureAssignmentBaseFormMixin
):
    class Meta(FeatureAssignmentBaseFormMixin.Meta):
        fields = ["person"] + FeatureAssignmentBaseFormMixin.Meta.fields

    def __init__(self, feature, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.instance.feature = feature

        self._remove_not_collected_field(self.instance.feature)
        self._remove_non_valid_fields_by_type(self.instance.feature.feature_type)
        self._setup_fee_field()

        if feature.feature_type == Feature.Type.PERMISSION:
            self.fields["person"].queryset = Person.objects.exclude(
                featureassignment__feature=feature
            )

        self.helper.include_media = False

        if "fee" in self.fields:
            self.fields["fee"].initial = feature.fee


class FeatureForm(WithoutFormTagMixin, ModelForm):
    class Meta:
        model = Feature
        fields = [
            "name",
            "parent",
            "assignable",
            "fee",
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

        features = Feature.objects.filter(feature_type=feature_type)

        if self.instance is not None:
            features = features.exclude(pk=self.instance.pk)

        self.fields["parent"].queryset = features

        self.feature_type = feature_type

        if feature_type == Feature.Type.QUALIFICATION:
            self.fields.pop("fee")

        elif feature_type == Feature.Type.PERMISSION:
            self.fields.pop("fee")
            self.fields.pop("collect_issuers")
            self.fields.pop("collect_codes")
            self.fields.pop("tier")

        elif feature_type == Feature.Type.EQUIPMENT:
            self.fields.pop("collect_issuers")
            self.fields.pop("tier")

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
