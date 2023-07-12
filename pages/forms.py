from django.forms import ModelForm

from pages.models import Page


class PageEditForm(ModelForm):
    class Meta:
        model = Page
        fields = "__all__"
