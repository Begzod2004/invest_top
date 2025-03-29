from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from apps.users.models import User
from apps.payments.models import Payment
from apps.subscriptions.models import Subscription, SubscriptionPlan
from apps.signals.models import Signal
from apps.reviews.models import Review
from apps.instruments.models import Instrument
from .models import BroadcastMessage
import json
from apps.invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot
import asyncio
from asgiref.sync import sync_to_async

# Register models from other apps
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

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

# Register models
# admin.site.register(Subscription)
# admin.site.register(SubscriptionPlan)
# admin.site.register(Signal)
# admin.site.register(Review)
# admin.site.register(Instrument)
