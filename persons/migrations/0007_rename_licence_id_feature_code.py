# Generated by Django 4.2.2 on 2023-06-12 20:48

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0006_feature_assignable_feature_issuer_feature_licence_id"),
    ]

    operations = [
        migrations.RenameField(
            model_name="feature",
            old_name="licence_id",
            new_name="code",
        ),
    ]
