from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api/users', views.UserViewSet, basename='users')
router.register(r'api/signals', views.SignalViewSet, basename='signals')
router.register(r'api/subscriptions', views.SubscriptionViewSet, basename='subscriptions')
router.register(r'api/payments', views.PaymentViewSet, basename='payments')
router.register(r'api/reviews', views.ReviewViewSet, basename='reviews')
router.register(r'api/broadcast', views.BroadcastViewSet, basename='broadcast')

app_name = 'dashboard'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    path('verify/', views.VerifyUserView.as_view(), name='verify-user'),
] 