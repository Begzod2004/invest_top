from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignalViewSet

router = DefaultRouter()
router.register('signals', SignalViewSet)

app_name = 'signals'

urlpatterns = [
    path('', include(router.urls)),
]
