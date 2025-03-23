from django.contrib import admin
from .models import Signal

class SignalAdmin(admin.ModelAdmin):
    list_display = ('instrument', 'entry_price', 'created_at')
    list_filter = ('instrument',)
    search_fields = ('instrument__name',)
    readonly_fields = ('created_at',)

admin.site.register(Signal, SignalAdmin)
