from django.forms import ModelForm

from pages.models import Page
from vzs.forms import WithoutFormTagMixin


class PageEditForm(WithoutFormTagMixin, ModelForm):
    class Meta:
        model = Page
        fields = "__all__"
