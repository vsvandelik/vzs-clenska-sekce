# Generated by Django 4.2.2 on 2023-07-10 12:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0018_alter_feature_options_alter_group_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="feature",
            name="name",
            field=models.CharField(max_length=50, verbose_name="Název"),
        ),
    ]
