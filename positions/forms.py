from django.forms import ModelChoiceField, ModelForm
from django.utils.translation import gettext_lazy as _

from events.forms_bases import AgeLimitForm, AllowedPersonTypeForm, GroupMembershipForm
from features.models import Feature
from positions.models import EventPosition
from vzs.forms import WithoutFormTagMixin
from vzs.mixins import (
    RelatedAddMixin,
    RelatedAddOrRemoveFormMixin,
    RelatedRemoveMixin,
)


class PositionForm(WithoutFormTagMixin, ModelForm):
    class Meta:
        fields = ["name", "wage_hour"]
        model = EventPosition

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["wage_hour"].widget.attrs["min"] = 1


class AddRemoveFeatureRequirementPositionMixin(RelatedAddOrRemoveFormMixin):
    class Meta:
        fields = []
        model = EventPosition

    feature = ModelChoiceField(queryset=Feature.objects.all())
    instance_to_add_or_remove_field_name = "feature"

    def _get_instances(self):
        return self.instance.required_features


class AddFeatureRequirementPositionForm(
    RelatedAddMixin, AddRemoveFeatureRequirementPositionMixin
):
    error_message = _("Nepodařilo se přidat vlastnost, protože už je přidaná.")


class RemoveFeatureRequirementPositionForm(
    RelatedRemoveMixin, AddRemoveFeatureRequirementPositionMixin
):
    error_message = _("Nepodařilo se odebrat vlastnost, protože není přiřazená.")


class PositionAgeLimitForm(AgeLimitForm):
    class Meta(AgeLimitForm.Meta):
        model = EventPosition


class PositionGroupMembershipForm(GroupMembershipForm):
    class Meta(GroupMembershipForm.Meta):
        model = EventPosition


class PositionAllowedPersonTypeForm(AllowedPersonTypeForm):
    class Meta(AllowedPersonTypeForm.Meta):
        model = EventPosition
