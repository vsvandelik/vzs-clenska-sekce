# Generated by Django 4.2.3 on 2023-08-08 12:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0026_remove_staticgroup_group_ptr_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PersonType",
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
                    "person_type",
                    models.CharField(
                        choices=[
                            ("radny", "řádný člen"),
                            ("cekatel", "člen - čekatel"),
                            ("cestny", "čestný člen"),
                            ("dite", "dítě"),
                            ("externi", "externí spolupracovník"),
                            ("rodic", "rodič"),
                        ],
                        max_length=10,
                        unique=True,
                        verbose_name="Typ osoby",
                    ),
                ),
            ],
        ),
    ]
