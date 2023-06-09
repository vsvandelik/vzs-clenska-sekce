from django.forms import ModelForm, widgets

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


class FeatureAssignmentForm(ModelForm):
    # TODO: Date_expire after date_assigned
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
