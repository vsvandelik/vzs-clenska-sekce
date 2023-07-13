from django import forms
from django.forms import ModelForm, ValidationError, Form
from django.utils.translation import gettext_lazy as _

from google_integration import google_directory
from groups.models import StaticGroup


class StaticGroupForm(ModelForm):
    class Meta:
        model = StaticGroup
        exclude = ["members"]

    def clean_google_email(self):
        all_groups = google_directory.get_list_of_groups()

        emails_of_groups = [group["email"] for group in all_groups]

        if (
            self.cleaned_data["google_email"]
            and self.cleaned_data["google_email"] not in emails_of_groups
        ):
            raise ValidationError(
                _("E-mailová adresa Google skupiny neodpovídá žádné reálné skupině.")
            )

        return self.cleaned_data["google_email"]

    def clean(self):
        cleaned_data = super().clean()
        google_as_members_authority = cleaned_data.get("google_as_members_authority")
        google_email = cleaned_data.get("google_email")

        if google_as_members_authority and not google_email:
            raise ValidationError(
                _(
                    "Google nemůže být jako autorita členů skupiny v situaci, kdy není vyplněna emailová adresa skupiny."
                )
            )


class AddMembersStaticGroupForm(ModelForm):
    class Meta:
        model = StaticGroup
        fields = ["members"]


class AddRemovePersonToGroupForm(Form):
    group = forms.ModelChoiceField(queryset=StaticGroup.objects.all())

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop("person", None)
        super().__init__(*args, **kwargs)


class AddPersonToGroupForm(AddRemovePersonToGroupForm):
    def clean_group(self):
        group = self.cleaned_data["group"]

        if group.members.contains(self.person):
            raise forms.ValidationError(_("Daná osoba je již ve skupině."))

        return group


class RemovePersonFromGroupForm(AddRemovePersonToGroupForm):
    def clean_group(self):
        group = self.cleaned_data["group"]

        if not group.members.contains(self.person):
            raise forms.ValidationError(_("Daná osoba není ve skupině přiřazena."))

        return group