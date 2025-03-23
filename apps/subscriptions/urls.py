from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionViewSet, SubscriptionPlanViewSet

router = DefaultRouter()
router.register('plans', SubscriptionPlanViewSet)
router.register('', SubscriptionViewSet)

app_name = 'subscriptions'

urlpatterns = [
    path('', include(router.urls)),
]
