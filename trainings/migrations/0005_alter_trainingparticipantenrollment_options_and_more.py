# Generated by Django 4.2.3 on 2023-08-24 20:20

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0003_alter_personhourlyrate_hourly_rate"),
        ("trainings", "0004_alter_trainingweekdays_weekday"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="trainingparticipantenrollment",
            options={},
        ),
        migrations.AlterUniqueTogether(
            name="trainingparticipantenrollment",
            unique_together={("training", "person")},
        ),
    ]