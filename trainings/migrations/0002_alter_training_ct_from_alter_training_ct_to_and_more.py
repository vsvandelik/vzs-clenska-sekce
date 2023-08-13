# Generated by Django 4.2.3 on 2023-08-13 06:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0001_initial"),
        ("trainings", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="training",
            name="ct_from",
            field=models.TimeField(blank=True, null=True, verbose_name="Od*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="ct_to",
            field=models.TimeField(blank=True, null=True, verbose_name="Do*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="ne_from",
            field=models.TimeField(blank=True, null=True, verbose_name="Od*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="ne_to",
            field=models.TimeField(blank=True, null=True, verbose_name="Do*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="pa_from",
            field=models.TimeField(blank=True, null=True, verbose_name="Od*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="pa_to",
            field=models.TimeField(blank=True, null=True, verbose_name="Do*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="po_from",
            field=models.TimeField(blank=True, null=True, verbose_name="Od*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="po_to",
            field=models.TimeField(blank=True, null=True, verbose_name="Do*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="so_from",
            field=models.TimeField(blank=True, null=True, verbose_name="Od*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="so_to",
            field=models.TimeField(blank=True, null=True, verbose_name="Do*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="st_from",
            field=models.TimeField(blank=True, null=True, verbose_name="Od*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="st_to",
            field=models.TimeField(blank=True, null=True, verbose_name="Do*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="ut_from",
            field=models.TimeField(blank=True, null=True, verbose_name="Od*"),
        ),
        migrations.AlterField(
            model_name="training",
            name="ut_to",
            field=models.TimeField(blank=True, null=True, verbose_name="Do*"),
        ),
        migrations.AlterField(
            model_name="trainingoccurrence",
            name="missing_participants_excused",
            field=models.ManyToManyField(
                related_name="missing_participants_excused_set",
                through="trainings.TrainingOccurrenceAttendanceCompensationOpportunity",
                to="persons.person",
            ),
        ),
    ]
