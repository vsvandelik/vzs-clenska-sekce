from django.db import models
from django.utils.translation import gettext_lazy as _

from persons.models import Person


class Group(models.Model):
    class Meta:
        permissions = [("spravce_skupin", _("Správce skupin"))]

    name = models.CharField(_("Název skupiny"), max_length=255)
    google_email = models.EmailField(
        _("E-mailová adresa skupiny v Google Workspace"),
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    google_as_members_authority = models.BooleanField(
        _("Je Google autorita seznamu členů?")
    )


class StaticGroup(Group):
    members = models.ManyToManyField(Person, related_name="groups")


class DynamicGroup(Group):
    pass
