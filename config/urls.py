from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

# API versiyalash
# api_v1_patterns = [
#     path('', include('apps.urls')),  # Asosiy API endpointlar
#     path('dashboard/', include('apps.dashboard.urls')),  # Dashboard API endpointlar
# ]

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # API v1
    # path('api/v1/', include(api_v1_patterns)),
    
    # API dokumentatsiya
    path('', include('apps.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(
        url_name='schema'
    ), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(
        url_name='schema'
    ), name='redoc'),
]

# Static va media fayllar uchun URL lar (faqat development rejimida)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)