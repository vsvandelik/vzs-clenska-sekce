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


class PersonSearchForm(forms.Form):
    name = "person_search_form"

    person = forms.ModelChoiceField(
        required=False,
        queryset=userless_people,
        widget=forms.HiddenInput,
    )
    query = forms.CharField(required=False, label=_("Obsahuje"))
    form_id = forms.CharField(required=False, initial=name, widget=forms.HiddenInput)

    def search_people(self):
        if not self.is_valid():
            return userless_people.none()

        query = self.cleaned_data["query"]

        if query == "":
            return userless_people.all()

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
    form_id = forms.CharField(
        required=False, initial="person_select_form", widget=forms.HiddenInput
    )

    def handle(self, request, context):
        pass


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

    field_order = ["email", "password"]

    error_messages = {
        "inactive": _("Tento uživatel je deaktivovaný."),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        forms.Form.__init__(self, *args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            person = Person.objects.filter(email=email).first()

            if person:
                self.user_cache = authenticate(
                    self.request, person=person, password=password
                )
                if self.user_cache:
                    self.confirm_login_allowed(self.user_cache)
                    return self.cleaned_data

        raise self.get_invalid_login_error()

    def get_invalid_login_error(self):
        return ValidationError(
            _("Prosím, zadejte správný e-mail a heslo"),
            code="invalid_login",
        )


class ChangeActivePersonForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    person = forms.ModelChoiceField(queryset=Person.objects.all())

    def clean_person(self):
        person = self.cleaned_data["person"]

        if person not in self.user.person.get_managed_persons():
            raise ValidationError(_("Uživatel nespravuje tuto osobu."))

        return person

    def clean(self):
        if not self.user.is_authenticated:
            raise ValidationError(_("Uživatel musí být přihlášen."))

        return self.cleaned_data
