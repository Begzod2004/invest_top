from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'subscriptions'

router = DefaultRouter()
router.register('payments', views.PaymentViewSet, basename='payment')
router.register('plans', views.SubscriptionPlanViewSet)
router.register('subscriptions', views.SubscriptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('status/', views.SubscriptionStatusView.as_view(), name='subscription-status'),
]
