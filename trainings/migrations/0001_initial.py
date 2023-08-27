# Generated by Django 4.2.3 on 2023-08-27 17:21

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("persons", "0001_initial"),
        ("transactions", "0001_initial"),
        ("events", "0001_initial"),
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
                (
                    "po_from",
                    models.TimeField(blank=True, null=True, verbose_name="Od*"),
                ),
                ("po_to", models.TimeField(blank=True, null=True, verbose_name="Do*")),
                (
                    "ut_from",
                    models.TimeField(blank=True, null=True, verbose_name="Od*"),
                ),
                ("ut_to", models.TimeField(blank=True, null=True, verbose_name="Do*")),
                (
                    "st_from",
                    models.TimeField(blank=True, null=True, verbose_name="Od*"),
                ),
                ("st_to", models.TimeField(blank=True, null=True, verbose_name="Do*")),
                (
                    "ct_from",
                    models.TimeField(blank=True, null=True, verbose_name="Od*"),
                ),
                ("ct_to", models.TimeField(blank=True, null=True, verbose_name="Do*")),
                (
                    "pa_from",
                    models.TimeField(blank=True, null=True, verbose_name="Od*"),
                ),
                ("pa_to", models.TimeField(blank=True, null=True, verbose_name="Do*")),
                (
                    "so_from",
                    models.TimeField(blank=True, null=True, verbose_name="Od*"),
                ),
                ("so_to", models.TimeField(blank=True, null=True, verbose_name="Do*")),
                (
                    "ne_from",
                    models.TimeField(blank=True, null=True, verbose_name="Od*"),
                ),
                ("ne_to", models.TimeField(blank=True, null=True, verbose_name="Do*")),
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
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("events.eventoccurrence",),
        ),
        migrations.CreateModel(
            name="TrainingWeekdays",
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
                    "weekday",
                    models.PositiveSmallIntegerField(
                        unique=True,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(6),
                        ],
                    ),
                ),
            ],
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
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="persons.person",
                        verbose_name="Osoba",
                    ),
                ),
                (
                    "training",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.training",
                    ),
                ),
                ("transactions", models.ManyToManyField(to="transactions.transaction")),
                (
                    "weekdays",
                    models.ManyToManyField(
                        related_name="training_weekdays_set",
                        to="trainings.trainingweekdays",
                    ),
                ),
            ],
            options={
                "unique_together": {("training", "person")},
            },
            bases=("events.participantenrollment",),
        ),
        migrations.CreateModel(
            name="TrainingOneTimeCoachPosition",
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
                    "coach_substitute_attendance",
                    models.CharField(
                        choices=[
                            ("nenastaveno", "nenastaveno"),
                            ("prezence", "prezence"),
                            ("absence", "absence"),
                        ],
                        max_length=11,
                    ),
                ),
                ("excuse_datetime", models.DateTimeField()),
                (
                    "coach_excused",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="coach_excused",
                        to="persons.person",
                    ),
                ),
                (
                    "coach_substitute",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="coach_substitute",
                        to="persons.person",
                    ),
                ),
                (
                    "training_occurrence",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trainings.trainingoccurrence",
                    ),
                ),
            ],
            options={
                "unique_together": {("training_occurrence", "coach_excused")},
            },
        ),
        migrations.CreateModel(
            name="TrainingOccurrenceAttendanceCompensationOpportunity",
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
                    "attendance",
                    models.CharField(
                        choices=[
                            ("nenastaveno", "nenastaveno"),
                            ("prezence", "prezence"),
                            ("absence", "absence"),
                        ],
                        max_length=11,
                    ),
                ),
                ("excuse_datetime", models.DateTimeField()),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="persons.person"
                    ),
                ),
                (
                    "training_occurrence_excused",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="training_occurrence_excused",
                        to="trainings.trainingoccurrence",
                    ),
                ),
                (
                    "training_occurrence_substitute",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="training_occurrence_substitute",
                        to="trainings.trainingoccurrence",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="trainingoccurrence",
            name="missing_coaches_excused",
            field=models.ManyToManyField(
                related_name="training_one_time_coach_position_set",
                through="trainings.TrainingOneTimeCoachPosition",
                to="persons.person",
            ),
        ),
        migrations.AddField(
            model_name="trainingoccurrence",
            name="missing_participants_excused",
            field=models.ManyToManyField(
                related_name="training_occurrence_attendance_compensation_opportunity_set",
                through="trainings.TrainingOccurrenceAttendanceCompensationOpportunity",
                to="persons.person",
            ),
        ),
        migrations.AddField(
            model_name="training",
            name="enrolled_participants",
            field=models.ManyToManyField(
                related_name="training_participant_enrollment_set",
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
        migrations.CreateModel(
            name="TrainingReplaceabilityForParticipants",
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
                    "training_1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="replaceable_training_1",
                        to="trainings.training",
                    ),
                ),
                (
                    "training_2",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="replaceable_training_2",
                        to="trainings.training",
                    ),
                ),
            ],
            options={
                "unique_together": {("training_1", "training_2")},
            },
        ),
        migrations.AddIndex(
            model_name="trainingoccurrenceattendancecompensationopportunity",
            index=models.Index(
                fields=["training_occurrence_substitute"],
                name="trainings_t_trainin_8791f0_idx",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="trainingoccurrenceattendancecompensationopportunity",
            unique_together={("training_occurrence_excused", "person")},
        ),
    ]
