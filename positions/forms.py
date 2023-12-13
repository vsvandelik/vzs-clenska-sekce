from django.forms import ModelChoiceField, ModelForm

from events.forms_bases import AgeLimitForm, AllowedPersonTypeForm, GroupMembershipForm
from features.models import Feature
from positions.models import EventPosition
from vzs.forms import WithoutFormTagMixin
from vzs.mixin_extensions import (
    RelatedAddMixin,
    RelatedAddOrRemoveMixin,
    RelatedRemoveMixin,
)


class PositionForm(WithoutFormTagMixin, ModelForm):
    class Meta:
        fields = ["name", "wage_hour"]
        model = EventPosition

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["wage_hour"].widget.attrs["min"] = 1


class AddRemoveFeatureRequirementPositionMixin(RelatedAddOrRemoveMixin, ModelForm):
    class Meta:
        fields = []
        model = EventPosition

    feature = ModelChoiceField(queryset=Feature.objects.all())

    def save(self, commit=True):
        instance = super().save(False)

        feature = self.cleaned_data["feature"]

        self._process_related_add_or_remove(instance.required_features, feature)

        if commit:
            instance.save()

        return instance


class AddFeatureRequirementPositionForm(
    RelatedAddMixin, AddRemoveFeatureRequirementPositionMixin
):
    pass


class RemoveFeatureRequirementPositionForm(
    RelatedRemoveMixin, AddRemoveFeatureRequirementPositionMixin
):
    pass


class PositionAgeLimitForm(AgeLimitForm):
    class Meta(AgeLimitForm.Meta):
        model = EventPosition


class PositionGroupMembershipForm(GroupMembershipForm):
    class Meta(GroupMembershipForm.Meta):
        model = EventPosition


class PositionAllowedPersonTypeForm(AllowedPersonTypeForm):
    class Meta(AllowedPersonTypeForm.Meta):
        model = EventPosition
