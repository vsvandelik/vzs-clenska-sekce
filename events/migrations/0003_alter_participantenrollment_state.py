# Generated by Django 4.2.3 on 2023-08-17 18:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="participantenrollment",
            name="state",
            field=models.CharField(
                choices=[
                    ("ceka", "čeká"),
                    ("schvalen", "schválen"),
                    ("nahradnik", "nahradník"),
                    ("odminut", "odmítnut"),
                ],
                max_length=10,
                verbose_name="Stav přihlášky",
            ),
        ),
    ]