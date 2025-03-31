from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'dashboard'

# API Router
router = DefaultRouter()

# Main endpoints
router.register('users', views.UserViewSet, basename='users')
router.register('signals', views.SignalViewSet, basename='signals')
router.register('subscriptions', views.SubscriptionViewSet, basename='subscriptions')
router.register('reviews', views.ReviewViewSet, basename='reviews')
router.register('instruments', views.InstrumentViewSet, basename='instruments')

# Broadcast endpoints
router.register('broadcast', views.BroadcastViewSet, basename='broadcast')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Auth verification
    path('auth/verify/', views.VerifyUserView.as_view(), name='verify-user'),
] 