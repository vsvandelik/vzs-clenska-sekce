from django import forms
from django.forms import Form, ModelForm
from persons.models import Person
from features.models import Feature
from positions.models import EventPosition
from django.forms.widgets import CheckboxInput
from django_select2.forms import Select2Widget


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


class AgeLimitForm(ModelForm):
    class Meta:
        model = EventPosition
        fields = ["min_age_enabled", "max_age_enabled", "min_age", "max_age"]
        labels = {
            "min_age_enabled": "Vyžadována",
            "max_age_enabled": "Vyžadována",
            "min_age": "Min",
            "max_age": "Max",
        }
        widgets = {
            "min_age_enabled": CheckboxInput(
                attrs={"onchange": "minAgeCheckboxClicked(this)"}
            ),
            "max_age_enabled": CheckboxInput(
                attrs={"onchange": "maxAgeCheckboxClicked(this)"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_age_enabled = cleaned_data["min_age_enabled"]
        max_age_enabled = cleaned_data["max_age_enabled"]

        if not min_age_enabled:
            cleaned_data["min_age"] = self.instance.min_age
        if not max_age_enabled:
            cleaned_data["max_age"] = self.instance.max_age

        fields = ["min_age", "max_age"]
        for f in fields:
            if eval(f"{f}_enabled"):
                if f not in cleaned_data or cleaned_data[f] is None:
                    self.add_error(f, "Toto pole je nutné vyplnit")

        if (
            len(cleaned_data) == 4
            and min_age_enabled
            and max_age_enabled
            and cleaned_data["min_age"] is not None
            and cleaned_data["max_age"] is not None
        ):
            if cleaned_data["min_age"] > cleaned_data["max_age"]:
                self.add_error(
                    "max_age",
                    "Hodnota minimální věkové hranice musí být menší nebo rovna hodnotě maximální věkové hranice",
                )
        return cleaned_data


class GroupMembershipForm(ModelForm):
    class Meta:
        model = EventPosition
        fields = ["group_membership_required", "group"]
        labels = {"group_membership_required": "Vyžadováno", "group": "Skupina"}
        widgets = {
            "group_membership_required": CheckboxInput(
                attrs={"onchange": "groupMembershipRequiredClicked(this)"}
            ),
            "group": Select2Widget(attrs={"onchange": "groupChanged(this)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].required = False

    def clean(self):
        cleaned_data = super().clean()
        group_membership_required = cleaned_data["group_membership_required"]
        if group_membership_required:
            if "group" not in cleaned_data or cleaned_data["group"] is None:
                self.add_error("group", "Toto pole je nutné vyplnit")
        else:
            if "group" in cleaned_data and cleaned_data["group"] is not None:
                self.add_error("group", "Toto pole musí být prázdné")
            else:
                cleaned_data["group"] = self.instance.group
        return cleaned_data


class PersonTypeForm(Form):
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
