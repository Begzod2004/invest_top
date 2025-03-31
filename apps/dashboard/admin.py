from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from .models import BroadcastMessage
from apps.subscriptions.models import Payment, Subscription
from apps.users.models import User

@admin.register(BroadcastMessage)
class BroadcastMessageAdmin(admin.ModelAdmin):
    list_display = [
        'recipient_type',
        'sent_by',
        'message',
        'sent_at',
        'success_count',
        'error_count'
    ]
    list_filter = [
        'recipient_type',
        'sent_at',
    ]
    readonly_fields = [
        'recipient_type',
        'message',
        'sent_by',
        'sent_at',
        'success_count',
        'error_count'
    ]
    search_fields = ['message']
    ordering = ['-sent_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
