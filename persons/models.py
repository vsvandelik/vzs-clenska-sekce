from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from vzs import models as vzs_models


class Person(vzs_models.RenderableModelMixin, models.Model):
    class Type(models.TextChoices):
        ADULT = "radny", _("řádný člen")
        EXPECTANT = "cekatel", _("člen - čekatel")
        HONORARY = "cestny", _("čestný člen")
        CHILD = "dite", _("dítě")
        EXTERNAL = "externi", _("externí spolupracovník")
        PARENT = "rodic", _("rodič")

    class HealthInsuranceCompany(models.TextChoices):
        VZP = 111, "111 - Všeobecná zdravotní pojišťovna České republiky"
        VOZP = 201, "201 - Vojenská zdravotní pojišťovna České republiky"
        CPZP = 205, "205 - Česká průmyslová zdravotní pojišťovna"
        OZP = (
            207,
            "207 - Oborová zdravotní pojišťovna zaměstnanců bank, pojišťoven a stavebnictví",
        )
        ZPS = 209, "209 - Zaměstnanecká pojišťovna Škoda"
        ZPMV = 211, "211 - Zdravotní pojišťovna ministerstva vnitra České republiky"
        RBP = 213, "213 - Revírní bratrská pokladna, zdravotní pojišťovna"

    class Sex(models.TextChoices):
        M = "M", _("muž")
        F = "F", _("žena")

    email = models.EmailField(_("E-mailová adressa"), unique=True)
    first_name = models.CharField(_("Křestní jméno"), max_length=50)
    last_name = models.CharField(_("Příjmení"), max_length=50)
    date_of_birth = models.DateField(_("Datum narození"), blank=True, null=True)
    sex = models.CharField(_("Pohlaví"), max_length=1, choices=Sex.choices)
    person_type = models.CharField(_("Typ osoby"), max_length=10, choices=Type.choices)
    birth_number = models.CharField(
        _("Rodné číslo"),
        max_length=11,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                r"\d{2}(0[1-9]|1[0-2]|5[1-9]|6[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])\/?\d{3,4}",
                _("Rodné číslo má špatný tvar."),
            )
        ],
    )
    health_insurance_company = models.CharField(
        _("Zdravotní pojišťovna"),
        max_length=3,
        choices=HealthInsuranceCompany.choices,
        blank=True,
        null=True,
    )
    phone = models.CharField(_("Telefon"), max_length=20, blank=True, null=True)
    street = models.CharField(
        _("Ulice a číslo popisné"), max_length=255, blank=True, null=True
    )
    city = models.CharField(_("Město"), max_length=255, blank=True, null=True)
    postcode = models.IntegerField(_("PSČ"), blank=True, null=True)
    swimming_time = models.CharField(
        _("Čas na 100m"),
        max_length=8,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                r"\d{2}:\d{2}\.\d{2}", _("Čas na 100m musí být v formátu mm:ss.ss.")
            )
        ],
    )
    features = models.ManyToManyField("persons.Feature", through="FeatureAssignment")
    managed_people = models.ManyToManyField("self", symmetrical=False)

    @property
    def address(self):
        if not (self.street and self.city and self.postcode):
            return None

        return f"{self.street}, {self.city}, {self.postcode}"

    def get_absolute_url(self):
        return reverse("persons:detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class QualificationsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(feature_type=Feature.Type.QUALIFICATION)


class PermissionsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(feature_type=Feature.Type.PERMISSION)


class EquipmentsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(feature_type=Feature.Type.EQUIPMENT)


class Feature(models.Model):
    class Type(models.TextChoices):
        QUALIFICATION = "K", _("kvalifikace")
        EQUIPMENT = "V", _("vybavení")
        PERMISSION = "O", _("oprávnění")

    objects = models.Manager()
    qualifications = QualificationsManager()
    permissions = PermissionsManager()
    equipments = EquipmentsManager()

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
    ),
    "permissions": FeatureTypeTextsClass(
        Feature.Type.PERMISSION,
        "oprávnění",
        "oprávnění",
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
        Feature.Type.EQUIPMENT,
        "vybavení",
        "vybavení",
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
    issuer = models.CharField(
        max_length=255, blank=True, null=True
    )  # Only for qualifications
    code = models.CharField(
        max_length=255, blank=True, null=True
    )  # Only for qualification + equipments

    class Meta:
        unique_together = ["person", "feature"]


class Group(models.Model):
    name = models.CharField(_("Název skupiny"), max_length=255)


class StaticGroup(Group):
    members = models.ManyToManyField(Person, related_name="groups")


class DynamicGroup(Group):
    pass


class Transaction(models.Model):
    amount = models.IntegerField()
    reason = models.CharField(max_length=150)
    date = models.DateField()
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    event = models.ForeignKey("events.Event", on_delete=models.SET_NULL, null=True)
