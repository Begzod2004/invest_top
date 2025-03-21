from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dashboard.admin import admin_site
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

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
    
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)