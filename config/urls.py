"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from dashboard.admin import admin_site
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


schema_view = get_schema_view(
   openapi.Info(
      title="Top Invest API",
      default_version='v1',
      description="""
      # Top Invest API Documentation
      
      ## Authentication
      This API uses JWT authentication. To authenticate:
      1. Get a token using the `/users/auth/login/` endpoint with Telegram authentication
      2. Include the token in the Authorization header: `Bearer <token>`
      
      ## API Endpoints
      
      ### Users
      - `/users/auth/login/` - Telegram authentication
      - `/users/api/users/{id}/send-message/` - Send message to a user
      
      ### Payments
      - `/payments/api/payments/` - List all payments
      - `/payments/api/payments/{id}/approve/` - Approve payment
      - `/payments/api/payments/{id}/reject/` - Reject payment
      - `/payments/api/payments/pending/` - List pending payments
      - `/payments/api/payments/approved/` - List approved payments
      - `/payments/api/payments/declined/` - List declined payments
      
      ### Subscriptions
      - `/subscriptions/api/plans/` - List subscription plans
      - `/subscriptions/api/plans/active/` - List active subscription plans
      - `/subscriptions/api/subscriptions/` - List all subscriptions
      - `/subscriptions/api/subscriptions/active/` - List active subscriptions
      - `/subscriptions/api/subscriptions/expired/` - List expired subscriptions
      - `/subscriptions/api/subscriptions/user/{id}/` - List user subscriptions
      - `/subscriptions/api/subscriptions/{id}/activate/` - Activate subscription
      - `/subscriptions/api/subscriptions/{id}/deactivate/` - Deactivate subscription
      - `/subscriptions/api/user/{id}/status/` - Get user subscription status
      
      ### Signals
      - `/signals/api/signals/` - List all signals
      - `/signals/api/signals/latest/` - List latest signals
      - `/signals/api/signals/pending/` - List pending signals
      - `/signals/api/signals/{id}/send/` - Send signal to Telegram channel
      
      ### Dashboard
      - `/dashboard/api/broadcast/` - List broadcast messages
      - `/dashboard/api/broadcast/send/` - Send broadcast message
      - `/dashboard/api/broadcast/send-all/` - Send to all users
      - `/dashboard/api/broadcast/send-active/` - Send to active users
      - `/dashboard/api/broadcast/send-subscribed/` - Send to subscribed users
      """,
      terms_of_service="https://www.topinvest.uz/terms/",
      contact=openapi.Contact(email="admin@topinvest.uz"),
      license=openapi.License(name="Commercial License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin_site.urls),
    path('api-auth/', include('rest_framework.urls')),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # App URLs
    path('users/', include('users.urls')),
    path('instruments/', include('instruments.urls')),
    path('payments/', include('payments.urls')),
    path('reviews/', include('reviews.urls')),
    path('signals/', include('signals.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('dashboard/', include('dashboard.urls')),
    
    # Swagger/OpenAPI Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

