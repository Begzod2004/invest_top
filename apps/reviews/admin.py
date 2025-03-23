from django.contrib import admin
from .models import Review

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)

admin.site.register(Review, ReviewAdmin)
