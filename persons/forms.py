import datetime
import re

from crispy_forms.layout import Submit
from django.forms import ModelForm, widgets, ValidationError
from django.utils.translation import gettext_lazy as _

from vzs import settings
from vzs.forms import VZSDefaultFormHelper
from .models import Person, FeatureAssignment, Feature, StaticGroup


class PersonForm(ModelForm):
    class Meta:
        model = Person
        exclude = ["features", "managed_people"]
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

        if self.instance.pk is not None:
            self.fields.pop("feature")

            if self.instance.feature.never_expires is True:
                self.fields.pop("date_expire")

        if feature_type == Feature.Type.PERMIT:
            self.fields.pop("issuer")
            self.fields.pop("code")

        elif feature_type == Feature.Type.POSSESSION:
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

    def clean_code(self):
        code = self.cleaned_data["code"]
        feature = self._get_feature(self.cleaned_data)

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

    def __init__(self, *args, **kwargs):
        feature_type = kwargs.pop("feature_type", None)
        super().__init__(*args, **kwargs)
        if feature_type:
            self.fields["parent"].queryset = Feature.objects.filter(
                feature_type=feature_type
            )


class StaticGroupForm(ModelForm):
    class Meta:
        model = StaticGroup
        fields = ["name"]


class AddMembersStaticGroupForm(ModelForm):
    class Meta:
        model = StaticGroup
        fields = ["members"]
