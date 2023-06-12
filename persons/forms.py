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
    # TODO: Hide Date_expire when its unlimited
    class Meta:
        model = FeatureAssignment
        fields = ["feature", "date_assigned", "date_expire"]
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
                feature_type=feature_type
            )

    def clean_date_expire(self):
        date_expire_value = self.cleaned_data["date_expire"]
        date_assigned_value = self.cleaned_data["date_assigned"]
        feature_value = self.cleaned_data["feature"]

        if feature_value.never_expires and date_expire_value is not None:
            raise ValidationError(
                _("Je vyplněné datum expirace u kvalifikace s neomezenou platností.")
            )

        elif (
            date_expire_value
            and date_assigned_value
            and date_assigned_value > date_expire_value
        ):
            raise ValidationError(_("Datum expirace je nižší než datum přiřazení."))

        return date_expire_value


class FeatureForm(ModelForm):
    class Meta:
        model = Feature
        fields = "__all__"
        exclude = ["feature_type"]

        labels = {
            "tier": _("Poplatek"),
            "name": _("Název"),
            "parent": _("Nadřazená kategorie"),
        }

    def __init__(self, *args, **kwargs):
        feature_type = kwargs.pop("feature_type", None)
        super().__init__(*args, **kwargs)
        if feature_type:
            self.fields["parent"].queryset = Feature.objects.filter(
                feature_type=feature_type
            )
