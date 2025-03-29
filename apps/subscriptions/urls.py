from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionPlanViewSet, 
    SubscriptionViewSet, 
    SubscriptionStatusView,
    PaymentCreateView,
    PaymentUploadScreenshotView,
    user_subscription_status
)

router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet)
router.register(r'subscriptions', SubscriptionViewSet)

app_name = 'subscriptions'

urlpatterns = [
    path('', include(router.urls)),
    path('status/', SubscriptionStatusView.as_view(), name='subscription_status'),
    path('payment/create/', PaymentCreateView.as_view(), name='payment_create'),
    path('payment/upload-screenshot/', PaymentUploadScreenshotView.as_view(), name='payment_upload_screenshot'),
    path('user/<str:user_id>/status/', user_subscription_status, name='user_subscription_status'),
]
