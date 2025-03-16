from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api/payments', views.PaymentViewSet, basename='payment')

app_name = 'payments'

urlpatterns = [
    # Admin panel actions (legacy)
    path('admin/payments/payment/approve/<int:payment_id>/', views.approve_payment, name='approve_payment'),
    path('admin/payments/payment/reject/<int:payment_id>/', views.reject_payment, name='reject_payment'),
    
    # API endpoints
    path('api/', include(router.urls)),
] 