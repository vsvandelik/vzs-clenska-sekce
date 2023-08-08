# Generated by Django 4.2.3 on 2023-08-08 08:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0019_persontype_event_allowed_person_types"),
        ("positions", "0006_alter_eventposition_name"),
    ]

    operations = [
        migrations.DeleteModel(
            name="PersonType",
        ),
        migrations.AlterField(
            model_name="eventposition",
            name="allowed_person_types",
            field=models.ManyToManyField(to="events.persontype"),
        ),
    ]
