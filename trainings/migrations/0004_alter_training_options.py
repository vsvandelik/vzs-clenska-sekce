# Generated by Django 5.0 on 2023-12-26 17:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trainings', '0003_alter_training_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='training',
            options={'base_manager_name': 'objects'},
        ),
    ]