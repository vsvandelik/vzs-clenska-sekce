# Generated by Django 4.2.7 on 2023-11-24 21:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("features", "0003_alter_featureassignment_unique_together_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="featureassignment",
            name="expiry_email_sent",
            field=models.BooleanField(default=False),
        ),
    ]