# Generated by Django 4.2.3 on 2023-08-28 14:41

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("events", "0001_initial"),
        ("persons", "0001_initial"),
        ("transactions", "0001_initial"),
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
                    "training_category",
                    models.CharField(
                        choices=[
                            ("lezecky", "lezecký"),
                            ("plavecky", "plavecký"),
                            ("zdravoveda", "zdravověda"),
                        ],
                        max_length=10,
                        null=True,
                        verbose_name="Kategorie tréninku",
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
            name="OrganizerOccurrenceAssignment",
            fields=[
                (
                    "organizerassignment_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="events.organizerassignment",
                    ),
                ),
                (
                    "occurrence",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="one_time_events.onetimeeventoccurrence",
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
            ],
            options={
                "unique_together": {("person", "occurrence")},
            },
            bases=("events.organizerassignment",),
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
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="Poplatek za účast*"
                    ),
                ),
                (
                    "one_time_event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="one_time_events.onetimeevent",
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
                    "transaction",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="transactions.transaction",
                    ),
                ),
            ],
            options={
                "unique_together": {("one_time_event", "person")},
            },
            bases=("events.participantenrollment",),
        ),
        migrations.CreateModel(
            name="OneTimeEventParticipantAttendance",
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
                    "enrollment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="one_time_events.onetimeeventparticipantenrollment",
                    ),
                ),
                (
                    "occurrence",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="one_time_events.onetimeeventoccurrence",
                    ),
                ),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="persons.person"
                    ),
                ),
            ],
            options={
                "unique_together": {("person", "occurrence")},
            },
        ),
        migrations.AddField(
            model_name="onetimeeventoccurrence",
            name="attending_participants",
            field=models.ManyToManyField(
                through="one_time_events.OneTimeEventParticipantAttendance",
                to="persons.person",
            ),
        ),
        migrations.AddField(
            model_name="onetimeeventoccurrence",
            name="organizers",
            field=models.ManyToManyField(
                related_name="organizer_occurrence_assignment_set",
                through="one_time_events.OrganizerOccurrenceAssignment",
                to="persons.person",
            ),
        ),
        migrations.AddField(
            model_name="onetimeevent",
            name="enrolled_participants",
            field=models.ManyToManyField(
                through="one_time_events.OneTimeEventParticipantEnrollment",
                to="persons.person",
            ),
        ),
    ]
