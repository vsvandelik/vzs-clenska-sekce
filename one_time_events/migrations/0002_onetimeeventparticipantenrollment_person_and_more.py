# Generated by Django 4.2.3 on 2023-08-19 16:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0003_alter_personhourlyrate_hourly_rate"),
        ("one_time_events", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="onetimeeventparticipantenrollment",
            name="person",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="persons.person",
                verbose_name="Osoba",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="onetimeevent",
            name="training_category",
            field=models.CharField(
                choices=[
                    ("lezecky", "lezecký"),
                    ("plavecky", "plavecký"),
                    ("zdravoveda", "zdravověda"),
                ],
                max_length=10,
                null=True,
                verbose_name="Kategorie tréninku",
            ),
        ),
        migrations.AlterField(
            model_name="onetimeeventparticipantenrollment",
            name="agreed_participation_fee",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Poplatek za účast*"
            ),
        ),
    ]
