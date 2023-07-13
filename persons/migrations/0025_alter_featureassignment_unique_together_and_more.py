# Generated by Django 4.2.2 on 2023-07-13 07:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transactions", "0002_alter_transaction_feature_assigment"),
        ("features", "0001_initial"),
        ("positions", "0002_alter_eventposition_required_features"),
        ("events", "0011_alter_event_requirements_and_more"),
        ("persons", "0024_delete_fiosettings_remove_transaction_event_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="featureassignment",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="featureassignment",
            name="feature",
        ),
        migrations.RemoveField(
            model_name="featureassignment",
            name="person",
        ),
        migrations.AlterField(
            model_name="person",
            name="features",
            field=models.ManyToManyField(
                through="features.FeatureAssignment", to="features.feature"
            ),
        ),
        migrations.DeleteModel(
            name="Feature",
        ),
        migrations.DeleteModel(
            name="FeatureAssignment",
        ),
    ]
