# Generated by Django 4.2.3 on 2023-08-19 13:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0003_alter_personhourlyrate_hourly_rate"),
        (
            "one_time_events",
            "0004_alter_onetimeeventparticipantenrollment_agreed_participation_fee",
        ),
    ]

    operations = [
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
            name="person",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="persons.person",
                verbose_name="Osoba",
            ),
        ),
    ]