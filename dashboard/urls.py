from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api/broadcast', views.BroadcastViewSet, basename='broadcast')

app_name = 'dashboard'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
] 