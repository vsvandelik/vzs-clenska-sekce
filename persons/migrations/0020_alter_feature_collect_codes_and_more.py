# Generated by Django 4.2.2 on 2023-07-10 13:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0019_alter_feature_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="feature",
            name="collect_codes",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="feature",
            name="collect_issuers",
            field=models.BooleanField(
                blank=True, null=True, verbose_name="Evidovat vydavatele kvalifikace"
            ),
        ),
        migrations.AlterField(
            model_name="feature",
            name="never_expires",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="feature",
            name="tier",
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, verbose_name="Poplatek"
            ),
        ),
    ]