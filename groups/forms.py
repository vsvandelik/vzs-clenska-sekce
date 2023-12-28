from django.forms import Form, ModelChoiceField, ModelForm, ValidationError
from django.utils.translation import gettext_lazy as _

from google_integration import google_directory
from groups.models import Group
from persons.models import Person
from vzs.forms import WithoutFormTagMixin
from vzs.mixin_extensions import (
    RelatedAddMixin,
    RelatedAddOrRemoveFormMixin,
    RelatedRemoveMixin,
)


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

        if google_as_members_authority is True and google_email is None:
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


class AddRemovePersonToGroupFormMixin(RelatedAddOrRemoveFormMixin):
    class Meta:
        fields = []
        model = Person

    group = ModelChoiceField(queryset=Group.objects.all())
    instance_to_add_or_remove_field_name = "group"

    def _get_instances(self):
        return self.instance.groups


class AddPersonToGroupForm(RelatedAddMixin, AddRemovePersonToGroupFormMixin):
    error_message = _("Daná osoba je již ve skupině.")


class RemovePersonFromGroupForm(RelatedRemoveMixin, AddRemovePersonToGroupFormMixin):
    error_message = _("Daná osoba není ve skupině přiřazena.")
