from django.db import models
from django.conf import settings

class Review(models.Model):
    STATUS_CHOICES = [
        ('pending_approval', 'Pending Approval'),
        ('admin_approved', 'Admin Approved'),
        ('admin_declined', 'Admin Declined'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_approval')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_reviews"
    )

    def __str__(self):
        return f"Review by {self.user.username} - {self.status}"
