from django import forms
from django.forms import Form, ModelForm, PasswordInput, Widget
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from persons.models import Person

from .models import User


class PersonSearchForm(Form):
    query = forms.CharField(required=False)


class NoRenderWidget(Widget):
    def render(self, *args, **kwargs):
        return ''


class UserCreationForm(ModelForm):
    class Meta:
        model = User
        fields = ['person', 'password']
        widgets = {
            'person': NoRenderWidget,
            'password': PasswordInput
        }
        labels = {
            'person': ''
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
