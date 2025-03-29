from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'dashboard'

# API Router
router = DefaultRouter()

# Statistics endpoints
router.register('staatsts/users', views.UserStatsViewSet, basename='user-stats')
router.register('st/payments', views.PaymentStatsViewSet, basename='payment-stats') 
router.register('stats/subscriptions', views.SubscriptionStatsViewSet, basename='subscription-stats')

# Broadcast endpoints
router.register('broadcast', views.BroadcastViewSet, basename='broadcast')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Auth verification
    path('auth/verify/', views.VerifyUserView.as_view(), name='verify-user'),
] 