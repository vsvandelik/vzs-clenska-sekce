# Generated by Django 4.2.3 on 2023-08-16 09:45

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("persons", "0001_initial"),
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OneTimeEvent",
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
                    "default_participation_fee",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Standardní výše poplatku pro účastníky",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("komercni", "komerční"),
                            ("kurz", "kurz"),
                            ("prezentacni", "prezentační"),
                        ],
                        max_length=11,
                        verbose_name="Druh události",
                    ),
                ),
                (
                    "participants_of_specific_training_requirement",
                    models.CharField(
                        choices=[
                            ("lezecky", "lezecký"),
                            ("plavecky", "plavecký"),
                            ("zdravoveda", "zdravověda"),
                        ],
                        max_length=10,
                        null=True,
                    ),
                ),
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
            bases=("events.event",),
        ),
        migrations.CreateModel(
            name="OneTimeEventOccurrence",
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
                ("date", models.DateField(verbose_name="Den konání")),
                (
                    "hours",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(10),
                        ],
                        verbose_name="Počet hodin",
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
            name="OneTimeEventParticipantEnrollment",
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
                    "agreed_participation_fee",
                    models.PositiveIntegerField(verbose_name="Poplatek za účast"),
                ),
                (
                    "one_time_event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="one_time_events.onetimeevent",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("events.participantenrollment",),
        ),
        migrations.CreateModel(
            name="OneTimeEventOccurrenceOrganizerPositionAssignment",
            fields=[
                (
                    "organizerpositionassignment_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="events.organizerpositionassignment",
                    ),
                ),
                (
                    "one_time_event_ocurrence",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="one_time_events.onetimeeventoccurrence",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("events.organizerpositionassignment",),
        ),
        migrations.AddField(
            model_name="onetimeeventoccurrence",
            name="organizers_assignment",
            field=models.ManyToManyField(
                to="one_time_events.onetimeeventoccurrenceorganizerpositionassignment"
            ),
        ),
        migrations.AddField(
            model_name="onetimeevent",
            name="enrolled_participants",
            field=models.ManyToManyField(
                related_name="one_time_event_participant_enrollment_set",
                through="one_time_events.OneTimeEventParticipantEnrollment",
                to="persons.person",
            ),
        ),
    ]
