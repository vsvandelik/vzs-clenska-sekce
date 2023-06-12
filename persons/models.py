from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Person(models.Model):
    class Type(models.TextChoices):
        CHILD = "dite", _("člen dítě")
        ADULT = "dospely", _("člen dospělý")
        EXPECTANT = "cekatel", _("člen čekatel")
        HONORARY = "cestny", _("čestný člen")
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
        "self", on_delete=models.CASCADE, default=None, blank=True, null=True
    )
    name = models.CharField(max_length=50, unique=True)
    never_expires = models.BooleanField(default=False)
    tier = models.PositiveSmallIntegerField(default=0)
    assignable = models.BooleanField(default=True)
    issuer = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=255, blank=True, null=True)

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
    ):
        self.shortcut = feature_type.value
        self.name_1 = feature_type.label
        self.name_4 = name_4
        self.form_labels = form_labels
        self.success_message_save = success_message_save
        self.success_message_delete = success_message_delete


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
            "issuer": _("Vydavatel"),
            "code": _("Kód osvědčení"),
        },
        _("Kvalifikace byla úspěšně uložena."),
        _("Kvalifikace byla úspěšně odstraněna."),
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
            "code": _("Invertární číslo"),
        },
        _("Vybavení bylo úspěšně uloženo."),
        _("Vybavení bylo úspěšně odstraněno."),
    ),
}


class FeatureAssignment(models.Model):
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    feature = models.ForeignKey("persons.Feature", on_delete=models.CASCADE)
    date_assigned = models.DateField()
    date_expire = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ["person", "feature"]


class Transaction(models.Model):
    amount = models.IntegerField()
    reason = models.CharField(max_length=150)
    date = models.DateField()
    person = models.ForeignKey("persons.Person", on_delete=models.CASCADE)
    event = models.ForeignKey("events.Event", on_delete=models.SET_NULL, null=True)
