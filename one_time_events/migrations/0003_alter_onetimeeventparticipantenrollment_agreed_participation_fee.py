# Generated by Django 4.2.3 on 2023-08-18 13:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("one_time_events", "0002_onetimeeventparticipantenrollment_person"),
    ]

    operations = [
        migrations.AlterField(
            model_name="onetimeeventparticipantenrollment",
            name="agreed_participation_fee",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Poplatek za účast"
            ),
        ),
    ]
