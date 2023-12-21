from itertools import chain

from django.contrib.auth.models import AnonymousUser
from django.core.validators import RegexValidator
from django.db.models import (
    CASCADE,
    Case,
    CharField,
    DateField,
    EmailField,
    ExpressionWrapper,
    ForeignKey,
    IntegerField,
    Manager,
    ManyToManyField,
    Model,
    PositiveIntegerField,
    Q,
    TextChoices,
    Value,
    When,
)
from django.db.models.functions import ExtractYear
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from features.models import Feature, FeatureAssignment
from vzs.models import ExportableCSVMixin, RenderableModelMixin
from vzs.utils import today


class PersonsManager(Manager):
    def get_queryset(self):
        return super().get_queryset()

    def with_age(self):
        date = today()
        return self.get_queryset().annotate(
            age=ExpressionWrapper(
                today().year
                - ExtractYear("date_of_birth")
                - Case(
                    When(Q(date_of_birth__month__gt=today().month), then=Value(1)),
                    When(
                        Q(date_of_birth__month=today().month)
                        & Q(date_of_birth__day__gt=today().day),
                        then=Value(1),
                    ),
                    default=Value(0),
                ),
                output_field=IntegerField(),
            )
        )


class Person(ExportableCSVMixin, RenderableModelMixin, Model):
    class Meta:
        permissions = [
            ("clenska_zakladna", _("Správce členské základny")),
            ("detska_clenska_zakladna", _("Správce dětské členské základny")),
            (
                "bazenova_clenska_zakladna",
                _("Správce bazénové dětské členské základny"),
            ),
            (
                "lezecka_clenska_zakladna",
                _("Správce lezecké dětské členské základny"),
            ),
            ("dospela_clenska_zakladna", _("Správce dospělé členské základny")),
        ]

    class Type(TextChoices):
        ADULT = "radny", _("řádný člen")
        EXPECTANT = "cekatel", _("člen - čekatel")
        HONORARY = "cestny", _("čestný člen")
        CHILD = "dite", _("dítě")
        EXTERNAL = "externi", _("externí spolupracovník")
        PARENT = "rodic", _("rodič")
        FORMER = "byvaly", _("bývalý člen")

    class HealthInsuranceCompany(TextChoices):
        VZP = "111", "111 - Všeobecná zdravotní pojišťovna České republiky"
        VOZP = "201", "201 - Vojenská zdravotní pojišťovna České republiky"
        CPZP = "205", "205 - Česká průmyslová zdravotní pojišťovna"
        OZP = (
            "207",
            "207 - Oborová zdravotní pojišťovna zaměstnanců bank, pojišťoven a stavebnictví",
        )
        ZPS = "209", "209 - Zaměstnanecká pojišťovna Škoda"
        ZPMV = "211", "211 - Zdravotní pojišťovna ministerstva vnitra České republiky"
        RBP = "213", "213 - Revírní bratrská pokladna, zdravotní pojišťovna"

    class Sex(TextChoices):
        M = "M", _("muž")
        F = "F", _("žena")

    objects = PersonsManager()

    email = EmailField(_("E-mailová adressa"), unique=True, blank=True, null=True)
    first_name = CharField(_("Křestní jméno"), max_length=50)
    last_name = CharField(_("Příjmení"), max_length=50)
    date_of_birth = DateField(_("Datum narození"), blank=True, null=True)
    sex = CharField(_("Pohlaví"), max_length=1, choices=Sex.choices)
    person_type = CharField(_("Typ osoby"), max_length=10, choices=Type.choices)
    birth_number = CharField(
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
    health_insurance_company = CharField(
        _("Zdravotní pojišťovna"),
        max_length=3,
        choices=HealthInsuranceCompany.choices,
        blank=True,
        null=True,
    )
    phone = CharField(_("Telefon"), max_length=20, blank=True, null=True)
    street = CharField(
        _("Ulice a číslo popisné"), max_length=255, blank=True, null=True
    )
    city = CharField(_("Město"), max_length=255, blank=True, null=True)
    postcode = IntegerField(_("PSČ"), blank=True, null=True)
    swimming_time = CharField(
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
    features = ManyToManyField(Feature, through=FeatureAssignment)
    managed_persons = ManyToManyField(
        "self", symmetrical=False, related_name="managed_by"
    )

    csv_order = [
        "person_type",
        "first_name",
        "last_name",
        "date_of_birth",
        "birth_number",
        "email",
        "phone",
        "city",
        "postcode",
        "street",
        "health_insurance_company",
        "swimming_time",
        "sex",
    ]

    @property
    def address(self):
        if not (self.street and self.city and self.postcode):
            return None

        return f"{self.street}, {self.city}, {self.postcode}"

    @property
    def formatted_phone(self):
        if not self.phone:
            return None

        return " ".join([self.phone[i : i + 3] for i in range(0, len(self.phone), 3)])

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse("persons:detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_managed_persons(self):
        return list(chain(self.managed_persons.all(), [self]))


def get_active_user(person: Person | None):
    if person is None:
        return AnonymousUser()

    return getattr(person, "user", AnonymousUser())


class PersonHourlyRate(Model):
    person = ForeignKey(Person, on_delete=CASCADE, related_name="hourly_rates")
    event_type = CharField(_("Kategorie akcí"), max_length=20)
    hourly_rate = PositiveIntegerField(
        _("Hodinová sazba"),
    )

    class Meta:
        unique_together = ["person", "event_type"]

    def __str__(self):
        return f"{self.person} - {self.event_type} - {self.hourly_rate} Kč / hod"

    @staticmethod
    def get_person_hourly_rates(person):
        items = PersonHourlyRate.objects.filter(person=person)

        return {entry.event_type: entry.hourly_rate for entry in items}
