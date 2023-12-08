from django.db import models
from django.utils.translation import gettext_lazy as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


class QualificationsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(feature_type=Feature.Type.QUALIFICATION)


class PermissionsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(feature_type=Feature.Type.PERMISSION)


class EquipmentsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(feature_type=Feature.Type.EQUIPMENT)


class Feature(MPTTModel):
    class Meta:
        permissions = [
            ("spravce_kvalifikaci", _("Správce kvalifikací")),
            ("spravce_opravneni", _("Správce oprávnění")),
            ("spravce_vybaveni", _("Správce vybavení")),
        ]

    class Type(models.TextChoices):
        QUALIFICATION = "K", _("kvalifikace")
        EQUIPMENT = "V", _("vybavení")
        PERMISSION = "O", _("oprávnění")

    objects = models.Manager()
    qualifications = QualificationsManager()
    permissions = PermissionsManager()
    equipments = EquipmentsManager()

    feature_type = models.CharField(max_length=1, choices=Type.choices)
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        default=None,
        blank=True,
        null=True,
        related_name="children",
        verbose_name=_("Nadřazená kategorie"),
    )
    name = models.CharField(_("Název"), max_length=50)
    assignable = models.BooleanField(_("Přiřaditelné osobě"), default=True)
    never_expires = models.BooleanField(blank=True, null=True)
    fee = models.PositiveSmallIntegerField(_("Poplatek"), blank=True, null=True)
    tier = models.PositiveSmallIntegerField(_("Úroveň"), blank=True, null=True)
    collect_issuers = models.BooleanField(
        _("Evidovat vydavatele kvalifikace"), blank=True, null=True
    )
    collect_codes = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return self.name


class FeatureTypeTextsClass:
    def __init__(
        self,
        feature_type,
        name_2,
        name_2_plural,
        name_4,
        form_labels,
        success_message_save,
        success_message_delete,
        success_message_assigned,
        success_message_assigning_updated,
        success_message_assigning_delete,
        duplicated_message_assigning,
        permission_name,
    ):
        self.shortcut = feature_type.value
        self.name_1 = feature_type.label
        self.name_2 = name_2
        self.name_2_plural = name_2_plural
        self.name_4 = name_4
        self.form_labels = form_labels
        self.success_message_save = success_message_save
        self.success_message_delete = success_message_delete
        self.success_message_assigned = success_message_assigned
        self.success_message_assigning_updated = success_message_assigning_updated
        self.success_message_assigning_delete = success_message_assigning_delete
        self.duplicated_message_assigning = duplicated_message_assigning
        self.permission_name = permission_name


FeatureTypeTexts = {
    "qualifications": FeatureTypeTextsClass(
        Feature.Type.QUALIFICATION,
        _("kvalifikace"),
        _("kvalifikací"),
        _("kvalifikaci"),
        {
            "feature": _("Název kvalifikace"),
            "date_assigned": _("Začátek platnost"),
            "date_expire": _("Konec platnosti"),
            "name": _("Název kvalifikace"),
            "never_expires": _("Neomezená platnost"),
            "collect_codes": _("Evidovat čísla osvědčení"),
            "issuer": _("Vydavatel"),
            "code": _("Kód osvědčení"),
        },
        _("Kvalifikace byla úspěšně uložena."),
        _("Kvalifikace byla úspěšně odstraněna."),
        _("Kvalifikace byla osobě úspěšně přidána."),
        _("Přiřazení kvalifikace bylo úspěšně upraveno."),
        _("Přiřazení kvalifikace bylo úspěšně odstraněno."),
        _("Daná osoba má již tuto kvalifikaci přiřazenou. Uložení se neprovedlo."),
        "features.spravce_kvalifikaci",
    ),
    "permissions": FeatureTypeTextsClass(
        Feature.Type.PERMISSION,
        _("oprávnění"),
        _("oprávnění"),
        _("oprávnění"),
        {
            "feature": _("Název oprávnění"),
            "date_assigned": _("Datum přiřazení"),
            "date_expire": _("Konec platnosti"),
            "name": _("Název oprávnění"),
            "never_expires": _("Neomezená platnost"),
        },
        _("Oprávnění bylo úspěšně uloženo."),
        _("Oprávnění bylo úspěšně odstraněno."),
        _("Oprávnění bylo osobě úspěšně přidáno."),
        _("Přiřazení oprávnění bylo úspěšně upraveno."),
        _("Přiřazení oprávnění bylo úspěšně odstraněno."),
        _("Daná osoba má již toto oprávnění přiřazené. Uložení se neprovedlo."),
        "features.spravce_opravneni",
    ),
    "equipments": FeatureTypeTextsClass(
        Feature.Type.EQUIPMENT,
        _("vybavení"),
        _("vybavení"),
        _("vybavení"),
        {
            "feature": _("Název vybavení"),
            "date_assigned": _("Datum zapůjčení"),
            "date_expire": _("Datum konce výpůjčky"),
            "date_returned": _("Datum reálného vrácení"),
            "name": _("Název vybavení"),
            "never_expires": _("Časově neomezená zápůjčka"),
            "collect_codes": _("Evidovat inventární číslo"),
            "code": _("Inventární číslo"),
            "fee": _("Poplatek"),
        },
        _("Vybavení bylo úspěšně uloženo."),
        _("Vybavení bylo úspěšně odstraněno."),
        _("Vybavení bylo osobě úspěšně přidáno."),
        _("Přiřazení vybavení bylo úspěšně upraveno."),
        _("Přiřazení vybavení bylo úspěšně odstraněno."),
        _("Daná osoba má již toto vybavení přiřazené. Uložení se neprovedlo."),
        "features.spravce_vybaveni",
    ),
}


class FeatureAssignment(models.Model):
    person = models.ForeignKey(
        "persons.Person", verbose_name=_("Osoba"), on_delete=models.CASCADE
    )
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    date_assigned = models.DateField()
    date_expire = models.DateField(null=True, blank=True)
    date_returned = models.DateField(null=True, blank=True)  # Only for equipments
    issuer = models.CharField(
        max_length=255, blank=True, null=True
    )  # Only for qualifications
    code = models.CharField(
        max_length=255, blank=True, null=True
    )  # Only for qualification + equipments
    expiry_email_sent = models.BooleanField(default=False)
