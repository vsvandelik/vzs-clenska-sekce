# Generated by Django 4.2.1 on 2023-05-30 12:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Feature",
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
                    "feature_type",
                    models.CharField(
                        choices=[
                            ("K", "kvalifikace"),
                            ("V", "vlastnictví"),
                            ("O", "oprávnění"),
                        ],
                        max_length=1,
                    ),
                ),
                ("category", models.CharField(max_length=20)),
                ("name", models.CharField(max_length=50, unique=True)),
                ("never_expires", models.BooleanField(default=False)),
                ("tier", models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="FeatureAssignment",
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
                ("date_assigned", models.DateField()),
                ("date_expire", models.DateField()),
                (
                    "feature",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="persons.feature",
                    ),
                ),
            ],
        ),
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
                ("email", models.EmailField(max_length=254, unique=True)),
                ("name", models.CharField(max_length=50)),
                ("date_of_birth", models.DateField()),
                (
                    "person_type",
                    models.CharField(
                        choices=[
                            ("dite", "člen dítě"),
                            ("dospely", "člen dospělý"),
                            ("cekatel", "člen čekatel"),
                            ("cestny", "čestný člen"),
                            ("externi", "externí spolupracovník"),
                            ("rodic", "rodič"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "features",
                    models.ManyToManyField(
                        through="persons.FeatureAssignment", to="persons.feature"
                    ),
                ),
                ("managed_people", models.ManyToManyField(to="persons.person")),
            ],
        ),
        migrations.CreateModel(
            name="Transaction",
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
                ("amount", models.IntegerField()),
                ("reason", models.CharField(max_length=150)),
                ("date", models.DateField()),
                (
                    "event",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="events.event",
                    ),
                ),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="persons.person"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="featureassignment",
            name="person",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="persons.person"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="featureassignment",
            unique_together={("person", "feature")},
        ),
    ]
