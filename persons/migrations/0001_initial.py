# Generated by Django 4.2.3 on 2023-08-27 19:24

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import vzs.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("features", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Person",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=254, unique=True, verbose_name="E-mailová adressa"
                    ),
                ),
                (
                    "first_name",
                    models.CharField(max_length=50, verbose_name="Křestní jméno"),
                ),
                ("last_name", models.CharField(max_length=50, verbose_name="Příjmení")),
                (
                    "date_of_birth",
                    models.DateField(
                        blank=True, null=True, verbose_name="Datum narození"
                    ),
                ),
                (
                    "sex",
                    models.CharField(
                        choices=[("M", "muž"), ("F", "žena")],
                        max_length=1,
                        verbose_name="Pohlaví",
                    ),
                ),
                (
                    "person_type",
                    models.CharField(
                        choices=[
                            ("radny", "řádný člen"),
                            ("cekatel", "člen - čekatel"),
                            ("cestny", "čestný člen"),
                            ("dite", "dítě"),
                            ("externi", "externí spolupracovník"),
                            ("rodic", "rodič"),
                            ("byvaly", "bývalý člen"),
                        ],
                        max_length=10,
                        verbose_name="Typ osoby",
                    ),
                ),
                (
                    "birth_number",
                    models.CharField(
                        blank=True,
                        max_length=11,
                        null=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "\\d{2}(0[1-9]|1[0-2]|5[1-9]|6[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])\\/?\\d{3,4}",
                                "Rodné číslo má špatný tvar.",
                            )
                        ],
                        verbose_name="Rodné číslo",
                    ),
                ),
                (
                    "health_insurance_company",
                    models.CharField(
                        blank=True,
                        choices=[
                            (
                                "111",
                                "111 - Všeobecná zdravotní pojišťovna České republiky",
                            ),
                            (
                                "201",
                                "201 - Vojenská zdravotní pojišťovna České republiky",
                            ),
                            ("205", "205 - Česká průmyslová zdravotní pojišťovna"),
                            (
                                "207",
                                "207 - Oborová zdravotní pojišťovna zaměstnanců bank, pojišťoven a stavebnictví",
                            ),
                            ("209", "209 - Zaměstnanecká pojišťovna Škoda"),
                            (
                                "211",
                                "211 - Zdravotní pojišťovna ministerstva vnitra České republiky",
                            ),
                            (
                                "213",
                                "213 - Revírní bratrská pokladna, zdravotní pojišťovna",
                            ),
                        ],
                        max_length=3,
                        null=True,
                        verbose_name="Zdravotní pojišťovna",
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True, max_length=20, null=True, verbose_name="Telefon"
                    ),
                ),
                (
                    "street",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Ulice a číslo popisné",
                    ),
                ),
                (
                    "city",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="Město"
                    ),
                ),
                (
                    "postcode",
                    models.IntegerField(blank=True, null=True, verbose_name="PSČ"),
                ),
                (
                    "swimming_time",
                    models.CharField(
                        blank=True,
                        max_length=8,
                        null=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "\\d{2}:\\d{2}\\.\\d{2}",
                                "Čas na 100m musí být v formátu mm:ss.ss.",
                            )
                        ],
                        verbose_name="Čas na 100m",
                    ),
                ),
                (
                    "features",
                    models.ManyToManyField(
                        through="features.FeatureAssignment", to="features.feature"
                    ),
                ),
                (
                    "managed_persons",
                    models.ManyToManyField(
                        related_name="managed_by", to="persons.person"
                    ),
                ),
            ],
            options={
                "permissions": [
                    ("clenska_zakladna", "Správce členské základny"),
                    ("detska_clenska_zakladna", "Správce dětské členské základny"),
                    (
                        "bazenova_clenska_zakladna",
                        "Správce bazénové dětské členské základny",
                    ),
                    (
                        "lezecka_clenska_zakladna",
                        "Správce lezecké dětské členské základny",
                    ),
                    ("dospela_clenska_zakladna", "Správce dospělé členské základny"),
                ],
            },
            bases=(
                vzs.models.ExportableCSVMixin,
                vzs.models.RenderableModelMixin,
                models.Model,
            ),
        ),
        migrations.CreateModel(
            name="PersonHourlyRate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "event_type",
                    models.CharField(max_length=20, verbose_name="Kategorie akcí"),
                ),
                (
                    "hourly_rate",
                    models.PositiveIntegerField(verbose_name="Hodinová sazba"),
                ),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="hourly_rates",
                        to="persons.person",
                    ),
                ),
            ],
            options={
                "unique_together": {("person", "event_type")},
            },
        ),
    ]
