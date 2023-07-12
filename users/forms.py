from django import forms
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.contrib.auth import password_validation, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from persons.models import Person
from .models import User, Permission


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
        password = self.cleaned_data["password"]
        password_validation.validate_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class UserCreateForm(UserBaseForm):
    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.person = person


class UserChangePasswordForm(UserBaseForm):
    pass


class UserChangePasswordOldAndRepeatForm(UserBaseForm):
    class Meta(UserBaseForm.Meta):
        labels = {"password": _("Nové heslo")}

    password_old = forms.CharField(
        label=_("Vaše staré heslo"), widget=forms.PasswordInput
    )
    password_repeat = forms.CharField(
        label=_("Zopakujte nové heslo"), widget=forms.PasswordInput
    )

    field_order = ["password_old", "password", "password_repeat"]

    def clean_password_old(self):
        password_old = self.cleaned_data["password_old"]

        user = self.instance

        if not user.check_password(password_old):
            raise ValidationError(_("Staré heslo se neshoduje."))

        return password_old

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_repeat = cleaned_data.get("password_repeat")

        if password != password_repeat:
            raise ValidationError(_("Nová hesla se neshodují."))

        return cleaned_data


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
            raise self.error

        user = authenticate(self.request, email=email, password=password)

        if not user:
            raise self.error

        self.user_cache = user
        return self.cleaned_data


class UserAssignRemovePermissionForm(forms.Form):
    permission = forms.ModelChoiceField(queryset=Permission.objects.all())


class ChangeActivePersonForm(forms.Form):
    person = forms.ModelChoiceField(queryset=Person.objects.all())
