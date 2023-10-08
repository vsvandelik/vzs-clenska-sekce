# Generated by Django 4.2.3 on 2023-09-18 16:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0003_alter_personhourlyrate_hourly_rate"),
        ("trainings", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="trainingoccurrence",
            old_name="attending_participants",
            new_name="participants",
        ),
        migrations.AddField(
            model_name="coachoccurrenceassignment",
            name="state",
            field=models.CharField(
                choices=[
                    ("prezence", "prezence"),
                    ("omluven", "omluven"),
                    ("neomluven", "neomluven"),
                ],
                default=1,
                max_length=9,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="trainingparticipantattendance",
            name="state",
            field=models.CharField(
                choices=[
                    ("prezence", "prezence"),
                    ("omluven", "omluven"),
                    ("neomluven", "neomluven"),
                ],
                default=1,
                max_length=9,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="trainingparticipantattendance",
            name="person",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="persons.person",
                verbose_name="Osoba",
            ),
        ),
    ]