from django import forms
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.db.models import Q
from django.contrib import messages

from persons.models import Person
from .models import User


class NoRenderWidget(forms.Widget):
    def render(self, *args, **kwargs):
        return ""


no_render_field = {"widget": NoRenderWidget, "label": ""}
userless_people = Person.objects.filter(user__isnull=True)


class CustomModelChoiceInput(forms.HiddenInput):
    """
    Renders a representation of the selected model choice
    in addition to the hidden input while also retaining the render order
    """

    input_type = None

    def __init__(self, queryset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = queryset

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)

        if value:
            obj = self.queryset.get(id=value)
            presentation_html = str(obj)
        else:
            presentation_html = ""

        return presentation_html + input_html

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["type"] = "hidden"
        return context


class CustomModelChoiceField(forms.ModelChoiceField):
    """
    ModelChoiceField with CustomModelChoiceInput with the same queryset as its widget
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, widget=CustomModelChoiceInput(queryset=kwargs["queryset"]), **kwargs
        )


class PersonSearchForm(forms.Form):
    name = "person_search_form"

    person = forms.ModelChoiceField(
        required=False, queryset=userless_people, widget=forms.HiddenInput
    )
    query = forms.CharField(required=False)
    show_all = forms.BooleanField(required=False)
    form_id = forms.CharField(
        required=False, initial="person_search_form", widget=forms.HiddenInput
    )

    def search_people(self):
        if not self.is_valid():
            return []

        if self.cleaned_data["show_all"]:
            return userless_people.all()

        query = self.cleaned_data["query"]

        if query == "":
            return []

        return userless_people.filter(
            Q(first_name__contains=query) | Q(last_name__contains=query)
        )

    def handle(self, request, context):
        context["people"] = self.search_people()


class PersonSelectForm(forms.Form):
    name = "person_select_form"

    person = forms.ModelChoiceField(
        required=False, queryset=userless_people, **no_render_field
    )
    query = forms.CharField(required=False, widget=forms.HiddenInput)
    show_all = forms.BooleanField(required=False, widget=forms.HiddenInput)
    form_id = forms.CharField(
        required=False, initial="person_select_form", widget=forms.HiddenInput
    )

    def handle(self, request, context):
        pass


class UserBaseForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["password"]
        widgets = {"password": forms.PasswordInput}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserCreateForm(UserBaseForm):
    class Meta(UserBaseForm.Meta):
        fields = UserBaseForm.Meta.fields + ["person"]

    person = CustomModelChoiceField(queryset=userless_people)

    field_order = ["person", "password"]


class UserSearchForm(forms.Form):
    name_query = forms.CharField(required=False)
    show_all = forms.BooleanField(required=False)

    def search_users(self):
        if not self.is_valid():
            return User.objects.none()

        if self.cleaned_data["show_all"]:
            return User.objects.all()

        query = self.cleaned_data["name_query"]

        if query == "":
            return User.objects.none()

        return User.objects.filter(
            Q(person__first_name__contains=query) | Q(person__last_name__contains=query)
        )


class UserSearchPaginationForm(forms.Form):
    name_query = forms.CharField(required=False, widget=forms.HiddenInput)
    show_all = forms.BooleanField(required=False, widget=forms.HiddenInput)
    page = forms.IntegerField(required=False, min_value=1, **no_render_field)


class UserEditForm(UserBaseForm):
    pass
