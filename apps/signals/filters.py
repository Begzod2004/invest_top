import django_filters
from .models import Signal

class SignalFilter(django_filters.FilterSet):
    """
    Signal modeli uchun filter set
    """
    created_at_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    is_active = django_filters.BooleanFilter()
    is_sent = django_filters.BooleanFilter()
    success_rate_min = django_filters.NumberFilter(field_name='success_rate', lookup_expr='gte')
    success_rate_max = django_filters.NumberFilter(field_name='success_rate', lookup_expr='lte')
    
    class Meta:
        model = Signal
        fields = {
            'signal_type': ['exact'],
            'instrument': ['exact'],
            'created_by': ['exact'],
        } 