# Generated by Django 4.2.2 on 2023-08-28 15:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        (
            "events",
            "0005_rename_participants_enroll_list_event_participants_enroll_state",
        ),
        ("transactions", "0002_bulktransaction_transaction_bulk_transaction"),
    ]

    operations = [
        migrations.AddField(
            model_name="bulktransaction",
            name="event",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="events.event",
                verbose_name="Událost",
            ),
        ),
    ]
