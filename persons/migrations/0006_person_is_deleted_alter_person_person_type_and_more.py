# Generated by Django 4.2.2 on 2023-12-29 10:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("persons", "0005_alter_person_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="is_deleted",
            field=models.BooleanField(default=False, verbose_name="Smazáno"),
        ),
        migrations.AlterField(
            model_name="person",
            name="person_type",
            field=models.CharField(
                choices=[
                    ("radny", "řádný člen"),
                    ("cekatel", "člen - čekatel"),
                    ("cestny", "čestný člen"),
                    ("dite", "dítě"),
                    ("externi", "externí spolupracovník"),
                    ("rodic", "rodič"),
                    ("byvaly", "bývalý člen"),
                    ("neznamy", "neznámý"),
                ],
                max_length=10,
                verbose_name="Typ osoby",
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="sex",
            field=models.CharField(
                choices=[("M", "muž"), ("F", "žena"), ("U", "neznámé")],
                max_length=1,
                verbose_name="Pohlaví",
            ),
        ),
    ]
