from django.contrib import admin
from signals.models import Signal

@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ("instrument", "order_type", "target_position", "stop_loss", "take_profit", "created_at")
    ordering = ("-created_at",)
