# Generated by Django 4.2.10 on 2025-03-30 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0003_remove_payment_payment_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="paymentmethod",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
