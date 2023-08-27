# Generated by Django 4.2.3 on 2023-08-27 19:24

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Page",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255, verbose_name="Titulek")),
                (
                    "content",
                    tinymce.models.HTMLField(
                        blank=True, null=True, verbose_name="Obsah"
                    ),
                ),
                (
                    "slug",
                    models.SlugField(max_length=255, unique=True, verbose_name="URL"),
                ),
                ("last_update", models.DateTimeField(auto_now=True)),
            ],
            options={
                "permissions": [("stranky", "Správce textových stránek")],
            },
        ),
    ]
