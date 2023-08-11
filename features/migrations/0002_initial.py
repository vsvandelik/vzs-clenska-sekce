# Generated by Django 4.2.3 on 2023-08-11 11:26

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("features", "0001_initial"),
        ("persons", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="featureassignment",
            name="person",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="persons.person",
                verbose_name="Osoba",
            ),
        ),
        migrations.AddField(
            model_name="feature",
            name="parent",
            field=mptt.fields.TreeForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="children",
                to="features.feature",
                verbose_name="Nadřazená kategorie",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="featureassignment",
            unique_together={("person", "feature")},
        ),
    ]
