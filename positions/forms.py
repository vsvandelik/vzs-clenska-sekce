from django import forms
from django.forms import Form, ModelForm
from persons.models import Person
from features.models import Feature
from persons.models import PersonType
from positions.models import EventPosition
from django_select2.forms import Select2Widget
from events.forms_bases import AgeLimitForm, GroupMembershipForm, AllowedPersonTypeForm


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


#
# class AddRemoveFeatureRequirementPositionForm(ModelForm):
#     class Meta:
#         fields = []
#         model = EventPosition
#
#     person_type = ChoiceField(choices=Person.Type.choices)
#
#     def clean(self):
#         cleaned_data = super().clean()
#         if "person_type" not in cleaned_data:
#             self.add_error(None, "Chybí hodnota person_type")
#         return cleaned_data
#
#     def save(self, commit=True):
#         person_type = self.cleaned_data["person_type"]
#         person_type_obj, _ = PersonType.objects.get_or_create(
#             person_type=person_type, defaults={"person_type": person_type}
#         )
#         if self.instance.allowed_person_types.contains(person_type_obj):
#             self.instance.allowed_person_types.remove(person_type_obj)
#         else:
#             self.instance.allowed_person_types.add(person_type_obj)
#         if commit:
#             self.instance.save()


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
