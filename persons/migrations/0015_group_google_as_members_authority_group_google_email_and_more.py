# Generated by Django 4.2.2 on 2023-06-22 12:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0014_alter_group_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="group",
            name="google_as_members_authority",
            field=models.BooleanField(
                default=False, verbose_name="Je Google autorita seznamu členů?"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="group",
            name="google_email",
            field=models.EmailField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="E-mailová adresa skupiny v Google Workspace",
            ),
        ),
        migrations.AlterField(
            model_name="feature",
            name="feature_type",
            field=models.CharField(
                choices=[("K", "kvalifikace"), ("V", "vybavení"), ("O", "oprávnění")],
                max_length=1,
            ),
        ),
    ]
