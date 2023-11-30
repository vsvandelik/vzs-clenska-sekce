from django.forms import Form, ModelChoiceField, ModelForm, ValidationError
from django.utils.translation import gettext_lazy as _

from google_integration import google_directory
from groups.models import Group
from persons.models import Person
from vzs.forms import WithoutFormTagMixin


class GroupForm(WithoutFormTagMixin, ModelForm):
    class Meta:
        model = Group
        exclude = ["members"]

    def clean_google_email(self):
        google_email = self.cleaned_data["google_email"]

        if google_email is not None:
            group_infos = google_directory.get_list_of_groups()

            emails_of_groups = (group_info.email for group_info in group_infos)

            if google_email not in emails_of_groups:
                raise ValidationError(
                    _(
                        "E-mailová adresa Google skupiny neodpovídá žádné reálné skupině."
                    )
                )

        return google_email

    def clean(self):
        cleaned_data = super().clean()

        google_as_members_authority = cleaned_data.get("google_as_members_authority")
        google_email = cleaned_data.get("google_email")

        if google_as_members_authority is not None and google_email is None:
            raise ValidationError(
                _(
                    "Google nemůže být jako autorita členů skupiny v situaci, "
                    "kdy není vyplněna emailová adresa skupiny."
                )
            )


class AddMembersGroupForm(ModelForm):
    class Meta:
        model = Group
        fields = ["members"]


class AddRemovePersonToGroupFormMixin(Form):
    group = ModelChoiceField(queryset=Group.objects.all())

    def __init__(self, *args, person: Person, **kwargs):
        self.person = person
        super().__init__(*args, **kwargs)


class AddPersonToGroupForm(AddRemovePersonToGroupFormMixin):
    def clean_group(self):
        group = self.cleaned_data["group"]

        if group.members.contains(self.person):
            raise ValidationError(_("Daná osoba je již ve skupině."))

        return group


class RemovePersonFromGroupForm(AddRemovePersonToGroupFormMixin):
    def clean_group(self):
        group = self.cleaned_data["group"]

        if not group.members.contains(self.person):
            raise ValidationError(_("Daná osoba není ve skupině přiřazena."))

        return group
