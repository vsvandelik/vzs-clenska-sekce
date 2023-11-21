from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.forms import (
    BooleanField,
    CharField,
    EmailField,
    Form,
    ModelChoiceField,
    ModelForm,
    PasswordInput,
    ValidationError,
)
from django.utils.translation import gettext_lazy as _

from persons.models import Person
from vzs.forms import WithoutFormTagMixin

from .models import Permission, ResetPasswordToken, User


class UserBaseForm(ModelForm):
    """
    Common base for forms that create and edit users.

    Handles password validation and password saving.

    **Request parameters**:

    *   ``password``
    """

    class Meta:
        """:meta private:"""

        model = User
        fields = ["password"]
        widgets = {"password": PasswordInput}

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


class UserCreateForm(WithoutFormTagMixin, UserBaseForm):
    """
    Creates a new user.

    :parameter person: The person associated with the new user.

    **Request parameters**:

    *   ``password``
    """

    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.person = person


class UserChangePasswordForm(WithoutFormTagMixin, UserBaseForm):
    """
    Changes an existing user's password.

    **Request parameters**:

    *   ``password``
    """

    pass


class UserChangePasswordRepeatForm(UserChangePasswordForm):
    """
    Changes an existing user's password.

    **Request parameters**:

    *   ``password``
    *   ``password_repeat`` - For validation purposes only.
    """

    class Meta(UserBaseForm.Meta):
        """:meta private:"""

        labels = {"password": _("Nové heslo")}

    password_repeat = CharField(label=_("Zopakujte nové heslo"), widget=PasswordInput)
    """:meta private:"""

    field_order = ["password", "password_repeat"]
    """:meta private:"""

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
    Changes an existing user's password.

    **Request parameters**:

    *   ``password``
    *   ``password_repeat`` - For validation purposes only.
    *   ``password_old`` - For validation purposes only.
    """

    password_old = CharField(label=_("Vaše staré heslo"), widget=PasswordInput)
    """:meta private:"""

    field_order = ["password_old", "password", "password_repeat"]
    """:meta private:"""

    def clean_password_old(self):
        """
        Validated that the submitted old password is correct.
        """

        password_old = self.cleaned_data["password_old"]

        user = self.instance

        if not user.check_password(password_old):
            raise ValidationError(_("Staré heslo se neshoduje."))

        return password_old


class LoginForm(WithoutFormTagMixin, AuthenticationForm):
    """
    Logs in users.

    **Request parameters**:

    *   ``email``
    *   ``password``
    """

    email = EmailField(label=_("E-mail"))
    """:meta private:"""

    username = None
    """:meta private:"""

    error = ValidationError(
        _("Prosím, zadejte správný e-mail a heslo"),
        code="invalid_login",
    )
    """:meta private:"""

    field_order = ["email", "password"]
    """:meta private:"""

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.user_cache: AbstractBaseUser | None = None

        Form.__init__(self, *args, **kwargs)

    def clean(self):
        """
        Tries to authenticate the user with the submitted email and password.
        """

        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email is None or password is None:
            raise self.error

        user = authenticate(self.request, email=email, password=password)

        if user is None:
            raise self.error

        self.user_cache = user
        return self.cleaned_data


class UserAssignRemovePermissionForm(Form):
    """
    Form for permission assignment manipulation.

    **Request parameters**:

    *   ``permission``
    """

    permission = ModelChoiceField(queryset=Permission.objects.all())
    """:meta private:"""


class ChangeActivePersonForm(Form):
    """
    Form for changing the active person.

    **Request parameters**:

    *   ``person``
    """

    person = ModelChoiceField(queryset=Person.objects.all())
    """:meta private:"""


class UserResetPasswordRequestForm(ModelForm):
    """
    Form for requesting a password reset.

    **Request parameters**:

    *   ``email``
    """

    class Meta:
        """:meta private:"""

        model = ResetPasswordToken
        fields = []

    email = EmailField(label=_("E-mail"))
    """:meta private:"""

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


class LogoutForm(Form):
    """
    Form for loggin out.

    **Request parameters**:

    *   ``remember`` - Whether to remember not to ask for logout confirmation again.
    """

    remember = BooleanField(required=False)
