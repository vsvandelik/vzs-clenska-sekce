from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Person(models.Model):
    class Type(models.TextChoices):
        ADULT = "radny", _("řádný člen")
        EXPECTANT = "cekatel", _("člen - čekatel")
        HONORARY = "cestny", _("čestný člen")
        CHILD = "dite", _("dítě")
        EXTERNAL = "externi", _("externí spolupracovník")
        PARENT = "rodic", _("rodič")

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    person_type = models.CharField(max_length=10, choices=Type.choices)
    features = models.ManyToManyField("persons.Feature", through="FeatureAssignment")
    managed_people = models.ManyToManyField("self", symmetrical=False)

    def get_absolute_url(self):
        return reverse("persons:detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Feature(models.Model):
    class Type(models.TextChoices):
        QUALIFICATION = "K", _("kvalifikace")
        POSSESSION = "V", _("vlastnictví")
        PERMIT = "O", _("oprávnění")

    feature_type = models.CharField(max_length=1, choices=Type.choices)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        default=None,
        blank=True,
        null=True,
        related_name="children",
        verbose_name=_("Nadřazená kategorie"),
    )
    name = models.CharField(_("Název"), max_length=50, unique=True)
    never_expires = models.BooleanField(default=False)
    tier = models.PositiveSmallIntegerField(_("Poplatek"), default=0)
    assignable = models.BooleanField(_("Přiřaditelné osobě"), default=True)
    collect_issuers = models.BooleanField(
        _("Evidovat vydavatele kvalifikace"), default=False
    )
    collect_codes = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class FeatureTypeTextsClass:
    def __init__(
        self,
        feature_type,
        name_4,
        form_labels,
        success_message_save,
        success_message_delete,
        success_message_assigned,
        success_message_assigning_updated,
        success_message_assigning_delete,
        duplicated_message_assigning,
    ):
        self.shortcut = feature_type.value
        self.name_1 = feature_type.label
        self.name_4 = name_4
        self.form_labels = form_labels
        self.success_message_save = success_message_save
        self.success_message_delete = success_message_delete
        self.success_message_assigned = success_message_assigned
        self.success_message_assigning_updated = success_message_assigning_updated
        self.success_message_assigning_delete = success_message_assigning_delete
        self.duplicated_message_assigning = duplicated_message_assigning


FeatureTypeTexts = {
    "qualifications": FeatureTypeTextsClass(
        Feature.Type.QUALIFICATION,
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
    ),
    "permissions": FeatureTypeTextsClass(
        Feature.Type.PERMIT,
        "oprávnění",
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
    ),
    "equipments": FeatureTypeTextsClass(
        Feature.Type.POSSESSION,
        "vybavení",
        {
            "feature": _("Název vybavení"),
            "date_assigned": _("Datum zapůjčení"),
            "date_expire": _("Datum vrácení"),
            "name": _("Název vybavení"),
            "never_expires": _("Časově neomezená zápůjčka"),
            "collect_codes": _("Evidovat inventární číslo"),
            "code": _("Inventární číslo"),
        },
        _("Vybavení bylo úspěšně uloženo."),
        _("Vybavení bylo úspěšně odstraněno."),
        _("Vybavení bylo osobě úspěšně přidáno."),
        _("Přiřazení vybavení bylo úspěšně upraveno."),
        _("Přiřazení vybavení bylo úspěšně odstraněno."),
        _("Daná osoba má již toto vybavení přiřazené. Uložení se neprovedlo."),
    ),
}


class FeatureAssignment(models.Model):
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    feature = models.ForeignKey("persons.Feature", on_delete=models.CASCADE)
    date_assigned = models.DateField()
    date_expire = models.DateField(null=True, blank=True)
    issuer = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ["person", "feature"]


class Transaction(models.Model):
    amount = models.IntegerField()
    reason = models.CharField(max_length=150)
    date = models.DateField()
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    event = models.ForeignKey("events.Event", on_delete=models.SET_NULL, null=True)
