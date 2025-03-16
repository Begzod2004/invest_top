from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api/signals', views.SignalViewSet, basename='signal')

app_name = 'signals'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # Legacy endpoints
    path('api/signals/create/', views.SignalCreateView.as_view(), name='signal-create'),
    path('api/signals/list/', views.SignalListView.as_view(), name='signal-list'),
    path('api/signals/<int:pk>/', views.SignalDetailView.as_view(), name='signal-detail'),
]
