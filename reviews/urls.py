from django.urls import path
from .views import ReviewCreateView, ReviewListView, ReviewDetailView, ReviewAdminUpdateView

urlpatterns = [
    path('create/', ReviewCreateView.as_view(), name='review-create'),
    path('list/', ReviewListView.as_view(), name='review-list'),
    path('<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('<int:pk>/update/', ReviewAdminUpdateView.as_view(), name='review-admin-update'),
]
