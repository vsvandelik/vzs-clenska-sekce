# Generated by Django 4.2.2 on 2023-06-23 08:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0014_alter_group_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="person",
            name="managed_people",
        ),
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
                unique=True,
                verbose_name="E-mailová adresa skupiny v Google Workspace",
            ),
        ),
        migrations.AddField(
            model_name="person",
            name="managed_persons",
            field=models.ManyToManyField(
                related_name="managed_by", to="persons.person"
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