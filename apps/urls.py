from django.urls import path, include


urlpatterns = [
    path('users/', include('apps.users.urls')),
    path('signals/', include('apps.signals.urls')),
    path('payments/', include('apps.payments.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('subscriptions/', include('apps.subscriptions.urls')),
    path('instruments/', include('apps.instruments.urls')),
]

