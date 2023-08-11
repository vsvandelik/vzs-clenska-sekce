# Generated by Django 4.2.3 on 2023-08-11 11:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("persons", "0001_initial"),
        ("events", "0001_initial"),
        ("groups", "0001_initial"),
        ("positions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventpositionassignment",
            name="position",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="positions.eventposition",
            ),
        ),
        migrations.AddField(
            model_name="eventoccurrenceorganizerpositionassignment",
            name="event_occurrence",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="events.eventoccurrence"
            ),
        ),
        migrations.AddField(
            model_name="eventoccurrenceorganizerpositionassignment",
            name="organizers",
            field=models.ManyToManyField(to="persons.person"),
        ),
        migrations.AddField(
            model_name="eventoccurrenceorganizerpositionassignment",
            name="position_assignment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="positions.eventposition",
            ),
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
            model_name="eventoccurrence",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_%(app_label)s.%(class)s_set+",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="allowed_person_types",
            field=models.ManyToManyField(to="persons.persontype"),
        ),
        migrations.AddField(
            model_name="event",
            name="group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="groups.group",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_%(app_label)s.%(class)s_set+",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="positions",
            field=models.ManyToManyField(
                through="events.EventPositionAssignment", to="positions.eventposition"
            ),
        ),
        migrations.AddField(
            model_name="enrollment",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="events.event"
            ),
        ),
        migrations.AddField(
            model_name="enrollment",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_%(app_label)s.%(class)s_set+",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="participantenrollment",
            name="person",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="persons.person"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="eventpositionassignment",
            unique_together={("event", "position")},
        ),
        migrations.AlterUniqueTogether(
            name="eventoccurrenceorganizerpositionassignment",
            unique_together={("event_occurrence", "position_assignment")},
        ),
    ]
