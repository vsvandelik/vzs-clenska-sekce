from django import forms
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.contrib.auth import password_validation, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from persons.models import Person
from .models import User, Permission


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
            obj = get_object_or_404(self.queryset, id=value)
            presentation_html = obj.render("inline")
        else:
            presentation_html = _("Vyberte osobu")

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


class PersonSelectForm(forms.Form):
    person = forms.ModelChoiceField(
        required=False, queryset=userless_people, **no_render_field
    )


class UserBaseForm(forms.ModelForm):
    """
    This form is the common base for both UserCreateForm and UserEditForm forms,
    as they both submit a password but only the Create form submits the person.
    """

    class Meta:
        model = User
        fields = ["password"]
        widgets = {"password": forms.PasswordInput}

    def clean_password(self):
        raw_password = self.cleaned_data["password"]
        password_validation.validate_password(raw_password)
        return raw_password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserCreateForm(UserBaseForm):
    class Meta(UserBaseForm.Meta):
        fields = UserBaseForm.Meta.fields + ["person"]

    person = CustomModelChoiceField(queryset=userless_people, label=_("Osoba"))

    field_order = ["person", "password"]


class UserSearchForm(forms.Form):
    name_query = forms.CharField(required=False, label=_("Obsahuje"))

    def search_users(self):
        if not self.is_valid():
            return User.objects.none()

        query = self.cleaned_data["name_query"]

        if query == "":
            return User.objects.all()

        return User.objects.filter(
            Q(person__first_name__contains=query) | Q(person__last_name__contains=query)
        )


class UserSearchPaginationForm(forms.Form):
    name_query = forms.CharField(required=False, widget=forms.HiddenInput)
    page = forms.IntegerField(required=False, min_value=1, **no_render_field)


class UserEditForm(UserBaseForm):
    pass


class LoginForm(AuthenticationForm):
    username = None
    email = forms.EmailField(label=_("E-mail"))

    error = ValidationError(
        _("Prosím, zadejte správný e-mail a heslo"),
        code="invalid_login",
    )

    field_order = ["email", "password"]

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        forms.Form.__init__(self, *args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if not email or not password:
            raise error

        user = authenticate(self.request, email=email, password=password)

        if not user:
            raise error

        self.user_cache = user
        return self.cleaned_data


class PermissionAssignForm(forms.Form):
    permission = forms.ModelChoiceField(queryset=Permission.objects.all())
