# Generated by Django 4.2.2 on 2023-07-10 18:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0020_alter_feature_collect_codes_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="feature_assigment",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="persons.featureassignment",
            ),
        ),
    ]
