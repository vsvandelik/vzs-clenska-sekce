# Generated by Django 4.2.2 on 2024-01-13 16:58

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("groups", "0002_alter_group_options"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="group",
            options={"ordering": ["name"]},
        ),
    ]