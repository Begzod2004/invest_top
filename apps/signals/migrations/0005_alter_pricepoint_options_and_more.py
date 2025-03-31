# Generated by Django 4.2.10 on 2025-03-30 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("signals", "0004_remove_signal_closed_at_remove_signal_success_rate_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="pricepoint",
            options={
                "ordering": ["price_type", "order"],
                "verbose_name": "Narx nuqtasi",
                "verbose_name_plural": "Narx nuqtalari",
            },
        ),
        migrations.RemoveField(
            model_name="pricepoint",
            name="description",
        ),
        migrations.RemoveField(
            model_name="signal",
            name="entry_prices",
        ),
        migrations.RemoveField(
            model_name="signal",
            name="leverage",
        ),
        migrations.RemoveField(
            model_name="signal",
            name="risk_percent",
        ),
        migrations.RemoveField(
            model_name="signal",
            name="stop_losses",
        ),
        migrations.RemoveField(
            model_name="signal",
            name="take_profits",
        ),
        migrations.RemoveField(
            model_name="signal",
            name="timeframe",
        ),
        migrations.AddField(
            model_name="signal",
            name="closed_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Yopilgan vaqt"
            ),
        ),
        migrations.AddField(
            model_name="signal",
            name="success_rate",
            field=models.FloatField(default=0, verbose_name="Muvaffaqiyat darajasi"),
        ),
    ]
