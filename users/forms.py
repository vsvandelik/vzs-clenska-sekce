from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from persons.models import Person
from vzs.forms import WithoutFormTagFormHelper

from .models import Permission, ResetPasswordToken, User


class UserBaseForm(forms.ModelForm):
    """
    Common base for the *user create* and *change password* forms.

    Handles password validation and password saving.
    """

    class Meta:
        model = User
        fields = ["password"]
        widgets = {"password": forms.PasswordInput}

    def clean_password(self):
        """
        Validates the password against the registered validators.
        """

        password = self.cleaned_data["password"]
        password_validation.validate_password(password)
        return password

    def save(self, commit=True):
        """
        Hashes the password before saving it.
        """

        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class UserCreateForm(UserBaseForm):
    """
    Form for creating a new user.

    Accepts a person as a `__init__` parameter and a password in the request body.
    """

    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.person = person

        self.helper = WithoutFormTagFormHelper()


class UserChangePasswordForm(UserBaseForm):
    """
    Form for changing an existing user's password.

    Accepts a password in the request body.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = WithoutFormTagFormHelper()


class UserChangePasswordRepeatForm(UserChangePasswordForm):
    """
    Form for changing an existing user's password.

    Accepts a password and a repeated password in the request body.
    """

    class Meta(UserBaseForm.Meta):
        labels = {"password": _("Nové heslo")}

    password_repeat = forms.CharField(
        label=_("Zopakujte nové heslo"), widget=forms.PasswordInput
    )

    field_order = ["password", "password_repeat"]

    def clean(self):
        """
        Validates that the two submitted passwords match.
        """

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_repeat = cleaned_data.get("password_repeat")

        if password != password_repeat:
            raise ValidationError(_("Nová hesla se neshodují."))

        return cleaned_data


class UserChangePasswordOldAndRepeatForm(UserChangePasswordRepeatForm):
    """
    Form for changing an existing user's password.

    Accepts the old password, a new password
    and a repeated password in the request body.
    """

    password_old = forms.CharField(
        label=_("Vaše staré heslo"), widget=forms.PasswordInput
    )

    field_order = ["password_old", "password", "password_repeat"]

    def clean_password_old(self):
        """
        Validated that the submitted old password is correct.
        """

        password_old = self.cleaned_data["password_old"]

        user = self.instance

        if not user.check_password(password_old):
            raise ValidationError(_("Staré heslo se neshoduje."))

        return password_old


class LoginForm(AuthenticationForm):
    """
    Form for logging in.

    Accepts the request in the `__init__` method.

    Accepts an email and a password in the request body.
    """

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

        self.helper = WithoutFormTagFormHelper()

        forms.Form.__init__(self, *args, **kwargs)

    def clean(self):
        """
        Tries to authenticate the user with the submitted email and password.
        """

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
    """
    Form for permission assignment manipulation.

    Accepts a permission in the request body.
    """

    permission = forms.ModelChoiceField(queryset=Permission.objects.all())


class ChangeActivePersonForm(forms.Form):
    """
    Form for changing the active person.

    Accepts a person in the request body.
    """

    person = forms.ModelChoiceField(queryset=Person.objects.all())


class UserResetPasswordRequestForm(forms.ModelForm):
    """
    Form for requesting a password reset.

    Accepts an email in the request body.
    """

    class Meta:
        model = ResetPasswordToken
        fields = []

    email = forms.EmailField(label=_("E-mail"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_found = False

    def save(self, commit=True):
        """
        Creates and saves a request token if a user with the submitted email exists.
        """

        token = super().save(commit=False)

        email = self.cleaned_data["email"]

        # We don't want to leak information about whether the email is valid or not.
        user = User.objects.filter(person__email=email).first()

        if user is not None:
            self.user_found = True
            token.user = user

            if commit:
                token.save()

        return token


class LogoutForm(forms.Form):
    """
    Form for loggin out.

    Accepts a boolean whether to remember not to ask for confirmation again.
    """

    remember = forms.BooleanField(required=False)
