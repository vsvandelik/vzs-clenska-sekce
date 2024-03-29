# Generated by Django 4.2.3 on 2023-11-20 10:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("positions", "0002_alter_eventposition_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="eventposition",
            name="name",
            field=models.CharField(
                error_messages={"unique": "Pozice s tímto názvem již existuje."},
                max_length=50,
                unique=True,
                verbose_name="Název",
            ),
        ),
    ]
