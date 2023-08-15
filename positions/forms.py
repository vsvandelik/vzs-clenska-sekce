from django import forms
from django.forms import Form, ModelForm
from persons.models import Person
from features.models import Feature
from persons.models import PersonType
from positions.models import EventPosition
from django_select2.forms import Select2Widget
from events.forms_bases import AgeLimitForm, GroupMembershipForm, AllowedPersonTypeForm


class PositionForm(ModelForm):
    class Meta:
        fields = ["name", "wage_hour"]
        model = EventPosition

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["wage_hour"].widget.attrs["min"] = 1


class AddRemoveFeatureRequirementPositionForm(ModelForm):
    class Meta:
        fields = []
        model = EventPosition

    feature_id = forms.IntegerField()

    def clean(self):
        cleaned_data = super().clean()
        fid = cleaned_data["feature_id"]
        try:
            cleaned_data["feature"] = Feature.objects.get(pk=fid)
        except Feature.DoesNotExist:
            self.add_error(
                "feature_id",
                f"Kvalifikace, oprávnění ani vybavení s id {fid} neexistuje",
            )
        return cleaned_data

    def save(self, commit=True):
        feature = self.cleaned_data["feature"]
        if self.instance.required_features.contains(feature):
            self.instance.required_features.remove(feature)
        else:
            self.instance.required_features.add(feature)
        if commit:
            self.instance.save()


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


class PositionAllowedPersonTypeForm(AllowedPersonTypeForm):
    class Meta:
        model = EventPosition
        fields = []
