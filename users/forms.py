from django import forms
from django.forms import Form, ModelForm, PasswordInput, Widget
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from persons.models import Person

from .models import User


class NoRenderWidget(Widget):
    def render(self, *args, **kwargs):
        return ''


no_render = {'widget': NoRenderWidget, 'label': ''}


class PersonSearchForm(Form):
    query = forms.CharField(required=False)
    show_all = forms.BooleanField(required=False, **no_render)

    def search_people(self):
        if not self.is_valid():
            return []

        userless = Person.objects.filter(user__isnull=True)

        if self.cleaned_data['show_all']:
            return userless.all()

        query = self.cleaned_data['query']

        if query == '':
            return []

        return userless.filter(name__contains=query)


class UserCreationForm(ModelForm):
    query = forms.CharField(required=False, widget=forms.HiddenInput)
    show_all = forms.BooleanField(required=False, widget=forms.HiddenInput)

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
