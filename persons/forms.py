from django.forms import ModelForm, widgets, ValidationError
from django.utils.translation import gettext_lazy as _

from vzs import settings
from .models import Person, FeatureAssignment, Feature


class PersonForm(ModelForm):
    class Meta:
        model = Person
        fields = ["email", "first_name", "last_name", "date_of_birth", "person_type"]
        widgets = {
            "date_of_birth": widgets.DateInput(
                format=settings.DATE_INPUT_FORMATS, attrs={"type": "date"}
            )
        }
        labels = {
            "email": _("E-mailová adresa"),
            "first_name": _("Křestní jméno"),
            "last_name": _("Příjmení"),
            "date_of_birth": _("Datum narození"),
            "person_type": _("Typ osoby"),
        }


class FeatureAssignmentForm(ModelForm):
    # TODO: Hide Date_expire, issuer and code when its not necessary
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

    def clean_date_expire(self):
        date_expire_value = self.cleaned_data["date_expire"]
        feature_value = self.cleaned_data["feature"]

        if feature_value.never_expires and date_expire_value is not None:
            raise ValidationError(
                _("Je vyplněné datum expirace u kvalifikace s neomezenou platností.")
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
        feature = self.cleaned_data["feature"]

        if not feature.collect_issuers and issuer is not None:
            raise ValidationError(
                _("Je vyplněn vydavatel u vlastnosti u které se vydavatel neeviduje.")
            )

    def clean_code(self):
        code = self.cleaned_data["code"]
        feature = self.cleaned_data["feature"]

        if not feature.collect_codes and code is not None:
            raise ValidationError(
                _(
                    "Je vyplněn kód vlastnosti u vlastnosti u které se vydavatel neeviduje."
                )
            )


class FeatureForm(ModelForm):
    class Meta:
        model = Feature
        fields = "__all__"
        exclude = ["feature_type"]

        labels = {
            "tier": _("Poplatek"),
            "name": _("Název"),
            "parent": _("Nadřazená kategorie"),
            "assignable": _("Přiřaditelné osobě"),
            "collect_issuers": _("Evidovat vydavatele kvalifikace"),
        }

    def __init__(self, *args, **kwargs):
        feature_type = kwargs.pop("feature_type", None)
        super().__init__(*args, **kwargs)
        if feature_type:
            self.fields["parent"].queryset = Feature.objects.filter(
                feature_type=feature_type
            )

            if feature_type == Feature.Type.PERMIT:
                self.fields.pop("issuer")
                self.fields.pop("code")

            elif feature_type == Feature.Type.POSSESSION:
                self.fields.pop("issuer")
