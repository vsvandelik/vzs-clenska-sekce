from django import forms
from django.forms import ModelForm
from django_select2.forms import Select2Widget

from events.forms_bases import AgeLimitForm, GroupMembershipForm, AllowedPersonTypeForm
from features.models import Feature
from positions.models import EventPosition


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
        instance = super().save(False)
        feature = self.cleaned_data["feature"]
        if instance.required_features.contains(feature):
            instance.required_features.remove(feature)
        else:
            instance.required_features.add(feature)
        if commit:
            instance.save()
        return instance


class PositionAgeLimitForm(AgeLimitForm):
    class Meta(AgeLimitForm.Meta):
        model = EventPosition


class PositionGroupMembershipForm(GroupMembershipForm):
    class Meta(GroupMembershipForm.Meta):
        model = EventPosition


class PositionAllowedPersonTypeForm(AllowedPersonTypeForm):
    class Meta(AllowedPersonTypeForm.Meta):
        model = EventPosition
