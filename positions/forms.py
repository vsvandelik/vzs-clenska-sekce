from django import forms
from django.forms import Form
from persons.models import Person
from features.models import Feature
from positions.models import EventPosition
from django_select2.forms import Select2Widget
from events.forms_bases import AgeLimitForm, GroupMembershipForm


class AddFeatureRequirementToPositionForm(Form):
    feature_id = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        self._position_id = kwargs.pop("position_id")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["position_id"] = self._position_id
        pid = cleaned_data["position_id"]
        fid = cleaned_data["feature_id"]
        try:
            cleaned_data["feature"] = Feature.objects.get(pk=fid)
            cleaned_data["position"] = EventPosition.objects.get(pk=pid)
        except EventPosition.DoesNotExist:
            self.add_error("position_id", f"Pozice s id {pid} neexistuje")
        except Feature.DoesNotExist:
            self.add_error(
                "feature_id",
                f"Kvalifikace, oprávnění ani vybavení s id {fid} neexistuje",
            )
        return cleaned_data


class PositionAgeLimitForm(AgeLimitForm):
    class Meta:
        model = EventPosition
        fields = ["min_age", "max_age"]


class PositionGroupMembershipForm(GroupMembershipForm):
    class Meta:
        model = EventPosition
        fields = ["group"]
        labels = {"group": "Skupina"}
        widgets = {
            "group": Select2Widget(attrs={"onchange": "groupChanged(this)"}),
        }


class PersonTypePositionForm(Form):
    person_type = forms.ChoiceField(choices=Person.Type.choices)

    def __init__(self, *args, **kwargs):
        self._position_id = kwargs.pop("position_id")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["position_id"] = self._position_id
        pid = cleaned_data["position_id"]
        try:
            cleaned_data["position"] = EventPosition.objects.get(pk=pid)
        except EventPosition.DoesNotExist:
            self.add_error("position_id", f"Pozice s id {pid} neexistuje")

        return cleaned_data
