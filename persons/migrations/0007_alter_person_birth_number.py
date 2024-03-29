# Generated by Django 4.2.2 on 2023-12-30 19:45

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0006_person_is_deleted_alter_person_person_type_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="birth_number",
            field=models.CharField(
                blank=True,
                max_length=11,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        "\\d{2}(0[1-9]|1[0-2]|5[1-9]|6[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])\\/\\d{3,4}",
                        "Rodné číslo má špatný tvar.",
                    )
                ],
                verbose_name="Rodné číslo",
            ),
        ),
    ]
