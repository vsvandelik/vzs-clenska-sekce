from django.db.models import BooleanField, CharField, EmailField, ManyToManyField, Model
from django.utils.translation import gettext_lazy as _

from persons.models import Person


class Group(Model):
    class Meta:
        permissions = [("spravce_skupin", _("Správce skupin"))]

    name = CharField(_("Název skupiny"), max_length=255)
    google_email = EmailField(
        _("E-mailová adresa skupiny v Google Workspace"),
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    google_as_members_authority = BooleanField(_("Je Google autorita seznamu členů?"))
    members = ManyToManyField(Person, related_name="groups")

    def __str__(self):
        email_out = f" <{self.google_email}>" if self.google_email is not None else ""

        return f"{self.name}{email_out}"
