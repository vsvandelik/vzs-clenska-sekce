from django.core.validators import RegexValidator
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
    health_insurance_company = models.SmallIntegerField(
        _("Zdravotní pojišťovna"),
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

    def get_absolute_url(self):
        return reverse("persons:detail", kwargs={"pk": self.pk})


class Feature(models.Model):
    class Type(models.TextChoices):
        QUALIFICATION = "K", _("kvalifikace")
        POSSESSION = "V", _("vlastnictví")
        PERMIT = "O", _("oprávnění")

    feature_type = models.CharField(max_length=1, choices=Type.choices)
    category = models.CharField(max_length=20)
    name = models.CharField(max_length=50, unique=True)
    never_expires = models.BooleanField(default=False)
    tier = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


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
