# Generated by Django 4.2.3 on 2023-08-11 20:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("events", "0001_initial"),
        ("persons", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Training",
            fields=[
                (
                    "event_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="events.event",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("lezecky", "lezecký"),
                            ("plavecky", "plavecký"),
                            ("zdravoveda", "zdravověda"),
                        ],
                        max_length=10,
                        verbose_name="Druh události",
                    ),
                ),
                ("po_from", models.TimeField(blank=True, null=True, verbose_name="Od")),
                ("po_to", models.TimeField(blank=True, null=True, verbose_name="Do")),
                ("ut_from", models.TimeField(blank=True, null=True, verbose_name="Od")),
                ("ut_to", models.TimeField(blank=True, null=True, verbose_name="Do")),
                ("st_from", models.TimeField(blank=True, null=True, verbose_name="Od")),
                ("st_to", models.TimeField(blank=True, null=True, verbose_name="Do")),
                ("ct_from", models.TimeField(blank=True, null=True, verbose_name="Od")),
                ("ct_to", models.TimeField(blank=True, null=True, verbose_name="Do")),
                ("pa_from", models.TimeField(blank=True, null=True, verbose_name="Od")),
                ("pa_to", models.TimeField(blank=True, null=True, verbose_name="Do")),
                ("so_from", models.TimeField(blank=True, null=True, verbose_name="Od")),
                ("so_to", models.TimeField(blank=True, null=True, verbose_name="Do")),
                ("ne_from", models.TimeField(blank=True, null=True, verbose_name="Od")),
                ("ne_to", models.TimeField(blank=True, null=True, verbose_name="Do")),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("events.event",),
        ),
        migrations.CreateModel(
            name="TrainingOccurrence",
            fields=[
                (
                    "eventoccurrence_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="events.eventoccurrence",
                    ),
                ),
                ("datetime_start", models.DateTimeField(verbose_name="Začíná")),
                ("datetime_end", models.DateTimeField(verbose_name="Končí")),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("neuzavrena", "neuzavřena"),
                            ("uzavrena", "uzavřena"),
                            ("zpracovana", "zpracována"),
                        ],
                        max_length=10,
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("events.eventoccurrence",),
        ),
        migrations.CreateModel(
            name="TrainingParticipantEnrollment",
            fields=[
                (
                    "participantenrollment_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="events.participantenrollment",
                    ),
                ),
                (
                    "training",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.training",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("events.participantenrollment",),
        ),
        migrations.AddField(
            model_name="training",
            name="enrolled_participants",
            field=models.ManyToManyField(
                related_name="enrolled_participants_set",
                through="trainings.TrainingParticipantEnrollment",
                to="persons.person",
            ),
        ),
        migrations.AddField(
            model_name="training",
            name="main_coach",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="persons.person",
            ),
        ),
    ]
