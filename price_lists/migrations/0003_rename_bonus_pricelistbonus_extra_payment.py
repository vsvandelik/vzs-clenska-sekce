# Generated by Django 4.2.3 on 2023-07-17 13:14

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("price_lists", "0002_rename_bonuses_pricelist_bonus_features_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="pricelistbonus",
            old_name="bonus",
            new_name="extra_payment",
        ),
    ]
