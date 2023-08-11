# Generated by Django 4.2.3 on 2023-08-10 19:50

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("positions", "0008_alter_eventposition_allowed_person_types"),
        ("persons", "0029_alter_persontype_person_type"),
        ("events", "0020_delete_persontype_alter_event_allowed_person_types"),
    ]

    operations = [
        migrations.CreateModel(
            name="Enrollment",
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
                ("datetime", models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name="EventOccurrence",
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
                    "state",
                    models.CharField(
                        choices=[
                            ("neuzavrena", "neuzavřena"),
                            ("uzavrena", "uzavřena"),
                            ("schvalena", "schválena"),
                        ],
                        max_length=10,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="EventOccurrenceOrganizerPositionAssignment",
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
                    "event_occurrence",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="events.eventoccurrence",
                    ),
                ),
                ("organizers", models.ManyToManyField(to="persons.person")),
                (
                    "position_assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="positions.eventposition",
                    ),
                ),
            ],
            options={
                "unique_together": {("event_occurrence", "position_assignment")},
            },
        ),
        migrations.AlterUniqueTogether(
            name="eventparticipation",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="eventparticipation",
            name="event",
        ),
        migrations.RemoveField(
            model_name="eventparticipation",
            name="person",
        ),
        migrations.AlterUniqueTogether(
            name="eventrequirement",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="eventrequirement",
            name="event",
        ),
        migrations.RemoveField(
            model_name="eventrequirement",
            name="feature",
        ),
        migrations.RemoveField(
            model_name="event",
            name="group_membership_required",
        ),
        migrations.RemoveField(
            model_name="event",
            name="min_age_enabled",
        ),
        migrations.RemoveField(
            model_name="event",
            name="parent",
        ),
        migrations.RemoveField(
            model_name="event",
            name="participants",
        ),
        migrations.RemoveField(
            model_name="event",
            name="price_list",
        ),
        migrations.RemoveField(
            model_name="event",
            name="state",
        ),
        migrations.RemoveField(
            model_name="event",
            name="time_end",
        ),
        migrations.RemoveField(
            model_name="event",
            name="time_start",
        ),
        migrations.RemoveField(
            model_name="eventpositionassignment",
            name="organizers",
        ),
        migrations.AddField(
            model_name="event",
            name="location",
            field=models.CharField(
                max_length=200, null=True, verbose_name="Místo konání"
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="max_age",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(99),
                ],
                verbose_name="Maximální věk účastníků",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="participants_of_specific_training_requirement",
            field=models.CharField(
                choices=[
                    ("lezecky", "lezecký"),
                    ("plavecky", "plavecký"),
                    ("zdravoveda", "zdravověda"),
                ],
                max_length=10,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="ParticipantEnrollment",
            fields=[
                (
                    "enrollment_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="events.enrollment",
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("ceka", "čeká"),
                            ("schvalen", "schválen"),
                            ("nahradnik", "nahradník"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="persons.person"
                    ),
                ),
            ],
            bases=("events.enrollment",),
        ),
        migrations.DeleteModel(
            name="EventOrganization",
        ),
        migrations.DeleteModel(
            name="EventParticipation",
        ),
        migrations.DeleteModel(
            name="EventRequirement",
        ),
        migrations.AddField(
            model_name="eventoccurrence",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="events.event"
            ),
        ),
        migrations.AddField(
            model_name="eventoccurrence",
            name="missing_organizers",
            field=models.ManyToManyField(
                related_name="missing_organizers_set", to="persons.person"
            ),
        ),
        migrations.AddField(
            model_name="eventoccurrence",
            name="missing_participants",
            field=models.ManyToManyField(
                related_name="missing_participants_set", to="persons.person"
            ),
        ),
        migrations.AddField(
            model_name="eventoccurrence",
            name="organizers_assignment",
            field=models.ManyToManyField(
                to="events.eventoccurrenceorganizerpositionassignment"
            ),
        ),
        migrations.AddField(
            model_name="enrollment",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="events.event"
            ),
        ),
    ]
