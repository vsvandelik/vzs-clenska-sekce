from django.forms import ModelForm, widgets

from vzs import settings
from .models import Person


class PersonForm(ModelForm):
    class Meta:
        model = Person
        fields = ["email", "first_name", "last_name", "date_of_birth", "person_type"]
        widgets = {
            "date_of_birth": widgets.DateInput(
                format=settings.DATE_INPUT_FORMATS, attrs={"type": "date"}
            )
        }
