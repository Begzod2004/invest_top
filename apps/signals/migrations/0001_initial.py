# Generated by Django 4.2.10 on 2025-03-29 11:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("instruments", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Signal",
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
                (
                    "signal_type",
                    models.CharField(
                        choices=[("BUY", "Sotib olish"), ("SELL", "Sotish")],
                        max_length=4,
                        verbose_name="Signal turi",
                    ),
                ),
                (
                    "entry_price",
                    models.DecimalField(
                        decimal_places=2, max_digits=10, verbose_name="Kirish narxi"
                    ),
                ),
                (
                    "take_profit",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        verbose_name="Take-profit narxi",
                    ),
                ),
                (
                    "stop_loss",
                    models.DecimalField(
                        decimal_places=2, max_digits=10, verbose_name="Stop-loss narxi"
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="Tavsif"),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True, null=True, upload_to="signals/", verbose_name="Rasm"
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Faol")),
                (
                    "is_sent",
                    models.BooleanField(default=False, verbose_name="Yuborilgan"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Yaratilgan vaqt"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Yangilangan vaqt"
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="signals",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Yaratuvchi",
                    ),
                ),
                (
                    "instrument",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="signals",
                        to="instruments.instrument",
                        verbose_name="Instrument",
                    ),
                ),
            ],
            options={
                "verbose_name": "Signal",
                "verbose_name_plural": "Signallar",
                "ordering": ["-created_at"],
            },
        ),
    ]
