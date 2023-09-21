from django.forms import ModelForm

from pages.models import Page
from vzs.forms import WithoutFormTagFormHelper


class PageEditForm(ModelForm):
    class Meta:
        model = Page
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = WithoutFormTagFormHelper()
