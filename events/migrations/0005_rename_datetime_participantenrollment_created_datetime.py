# Generated by Django 4.2.3 on 2023-08-19 15:13

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0004_alter_event_group_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="participantenrollment",
            old_name="datetime",
            new_name="created_datetime",
        ),
    ]
