from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api/subscriptions', views.SubscriptionViewSet, basename='subscription')
router.register(r'api/plans', views.SubscriptionPlanViewSet, basename='subscription-plan')

app_name = 'subscriptions'

urlpatterns = [
    # Legacy API endpoints
    path('status/', views.SubscriptionStatusView.as_view(), name='subscription-status'),
    path('payment/create/', views.PaymentCreateView.as_view(), name='payment-create'),
    path('payment/upload-screenshot/', views.PaymentUploadScreenshotView.as_view(), name='payment-upload-screenshot'),
    
    # New API endpoints
    path('', include(router.urls)),
    path('api/user/<int:user_id>/status/', views.user_subscription_status, name='user-subscription-status'),
]
