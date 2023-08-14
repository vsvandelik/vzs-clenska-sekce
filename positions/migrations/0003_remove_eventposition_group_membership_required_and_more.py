# Generated by Django 4.2.3 on 2023-08-14 12:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("groups", "0001_initial"),
        ("positions", "0002_remove_eventposition_max_age_enabled_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="eventposition",
            name="group_membership_required",
        ),
        migrations.AlterField(
            model_name="eventposition",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="groups.group",
            ),
        ),
    ]
