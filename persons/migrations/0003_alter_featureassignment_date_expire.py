# Generated by Django 4.2.2 on 2023-06-09 20:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0002_rename_name_person_first_name_person_last_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="featureassignment",
            name="date_expire",
            field=models.DateField(blank=True, null=True),
        ),
    ]
