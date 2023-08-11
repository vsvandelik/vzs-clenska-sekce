# Generated by Django 4.2.3 on 2023-08-11 16:57

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("persons", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Group",
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
                    "name",
                    models.CharField(max_length=255, verbose_name="Název skupiny"),
                ),
                (
                    "google_email",
                    models.EmailField(
                        blank=True,
                        max_length=255,
                        null=True,
                        unique=True,
                        verbose_name="E-mailová adresa skupiny v Google Workspace",
                    ),
                ),
                (
                    "google_as_members_authority",
                    models.BooleanField(
                        verbose_name="Je Google autorita seznamu členů?"
                    ),
                ),
                (
                    "members",
                    models.ManyToManyField(related_name="groups", to="persons.person"),
                ),
            ],
            options={
                "permissions": [("spravce_skupin", "Správce skupin")],
            },
        ),
    ]
