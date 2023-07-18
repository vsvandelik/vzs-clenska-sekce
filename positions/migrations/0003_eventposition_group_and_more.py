# Generated by Django 4.2.3 on 2023-07-13 19:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("groups", "0001_initial"),
        ("positions", "0002_alter_eventposition_required_features"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventposition",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="groups.group",
            ),
        ),
        migrations.AddField(
            model_name="eventposition",
            name="group_membership_required",
            field=models.BooleanField(default=False),
        ),
    ]