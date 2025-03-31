from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('signals', views.SignalViewSet)
router.register('price-points', views.PricePointViewSet)

app_name = 'signals'

urlpatterns = [
    path('', include(router.urls)),
    path('create/', views.SignalCreateView.as_view(), name='signal-create'),
]
