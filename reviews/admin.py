from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_at', 'updated_at', 'updated_admin')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'text')
    ordering = ('-created_at',)
    actions = ['approve_reviews', 'decline_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(status='admin_approved', updated_admin=request.user)
    approve_reviews.short_description = "Mark selected reviews as Approved"

    def decline_reviews(self, request, queryset):
        queryset.update(status='admin_declined', updated_admin=request.user)
    decline_reviews.short_description = "Mark selected reviews as Declined"
