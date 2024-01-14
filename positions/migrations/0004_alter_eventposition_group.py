# Generated by Django 4.2.2 on 2024-01-13 16:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("groups", "0003_alter_group_options"),
        ("positions", "0003_alter_eventposition_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="eventposition",
            name="group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="groups.group",
                verbose_name="Skupina",
            ),
        ),
    ]