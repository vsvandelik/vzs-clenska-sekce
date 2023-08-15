# Generated by Django 4.2.3 on 2023-08-15 09:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("one_time_events", "0003_alter_onetimeevent_enrolled_participants"),
    ]

    operations = [
        migrations.AlterField(
            model_name="onetimeevent",
            name="default_participation_fee",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Základní sazba poplatku pro účastníky",
            ),
        ),
    ]
