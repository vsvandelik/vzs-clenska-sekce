# Generated by Django 4.2.2 on 2023-10-02 14:45

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "trainings",
            "0002_rename_attending_participants_trainingoccurrence_participants_and_more",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="training",
            options={
                "permissions": [
                    ("lezecky", "Správce lezeckých tréninků"),
                    ("plavecky", "Správce plaveckých tréninků"),
                    ("zdravoveda", "Správce zdravovědy"),
                ]
            },
        ),
    ]
