import datetime
import re

from django.forms import ModelForm, widgets, ValidationError
from django.utils.translation import gettext_lazy as _

from vzs import settings
from .models import Person, FeatureAssignment, Feature


class PersonForm(ModelForm):
    class Meta:
        model = Person
        exclude = ["features", "managed_people"]
        widgets = {
            "date_of_birth": widgets.DateInput(
                format=settings.DATE_INPUT_FORMATS, attrs={"type": "date"}
            )
        }

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data["date_of_birth"]

        if date_of_birth and date_of_birth > datetime.date.today():
            raise ValidationError(_("Neplatné datum narození."))

        return date_of_birth

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
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

        if len(str(postcode)) != 5:
            raise ValidationError(_("PSČ nemá platný formát."))

        return postcode


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
