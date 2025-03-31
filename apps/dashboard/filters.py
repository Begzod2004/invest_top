from django_filters import rest_framework as filters
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.signals.models import Signal
from apps.subscriptions.models import Subscription
from apps.reviews.models import Review
from apps.instruments.models import Instrument

User = get_user_model()

class UserFilter(filters.FilterSet):
    """User modelini filterlash uchun"""
    username = filters.CharFilter(lookup_expr='icontains')
    email = filters.CharFilter(lookup_expr='icontains')
    first_name = filters.CharFilter(lookup_expr='icontains')
    last_name = filters.CharFilter(lookup_expr='icontains')
    phone = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    is_blocked = filters.BooleanFilter()
    is_verified = filters.BooleanFilter()
    created_at_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone',
            'is_active', 'is_blocked', 'is_verified',
            'created_at_after', 'created_at_before'
        ]

class SignalFilter(filters.FilterSet):
    """Signal modelini filterlash uchun"""
    user = filters.CharFilter(field_name='created_by__username', lookup_expr='icontains')
    symbol = filters.CharFilter(field_name='instrument__name', lookup_expr='icontains')
    type = filters.ChoiceFilter(field_name='signal_type', choices=Signal.SIGNAL_TYPES)
    is_active = filters.BooleanFilter()
    is_sent = filters.BooleanFilter()
    success_rate_min = filters.NumberFilter(field_name='success_rate', lookup_expr='gte')
    success_rate_max = filters.NumberFilter(field_name='success_rate', lookup_expr='lte')
    created_at_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Signal
        fields = [
            'user', 'symbol', 'type', 'is_active', 'is_sent',
            'success_rate_min', 'success_rate_max',
            'created_at_after', 'created_at_before'
        ]

class SubscriptionFilter(filters.FilterSet):
    """Subscription modelini filterlash uchun"""
    user = filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    plan = filters.CharFilter(field_name='plan__name', lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    expires_at_after = filters.DateTimeFilter(field_name='expires_at', lookup_expr='gte')
    expires_at_before = filters.DateTimeFilter(field_name='expires_at', lookup_expr='lte')
    created_at_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Subscription
        fields = [
            'user', 'plan', 'is_active',
            'expires_at_after', 'expires_at_before',
            'created_at_after', 'created_at_before'
        ]

class ReviewFilter(filters.FilterSet):
    """Review modelini filterlash uchun"""
    user = filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    rating = filters.NumberFilter()
    rating_min = filters.NumberFilter(field_name='rating', lookup_expr='gte')
    rating_max = filters.NumberFilter(field_name='rating', lookup_expr='lte')
    is_approved = filters.BooleanFilter()
    created_at_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Review
        fields = [
            'user', 'rating', 'rating_min', 'rating_max', 'is_approved',
            'created_at_after', 'created_at_before'
        ]

class InstrumentFilter(filters.FilterSet):
    """Instrument modelini filterlash uchun"""
    name = filters.CharFilter(lookup_expr='icontains')
    symbol = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    created_at_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Instrument
        fields = [
            'name', 'symbol', 'is_active',
            'created_at_after', 'created_at_before'
        ] 