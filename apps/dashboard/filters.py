from django_filters import rest_framework as filters
from apps.users.models import User
from apps.signals.models import Signal
from apps.subscriptions.models import Subscription
from apps.payments.models import Payment
from apps.reviews.models import Review
from apps.instruments.models import Instrument

class UserFilter(filters.FilterSet):
    username = filters.CharFilter(lookup_expr='icontains')
    first_name = filters.CharFilter(lookup_expr='icontains')
    last_name = filters.CharFilter(lookup_expr='icontains')
    phone_number = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    is_admin = filters.BooleanFilter()
    is_subscribed = filters.BooleanFilter()
    date_joined = filters.DateFromToRangeFilter()
    balance = filters.RangeFilter()
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone_number', 
                 'is_active', 'is_admin', 'is_subscribed', 'date_joined', 'balance']

class SignalFilter(filters.FilterSet):
    created_at = filters.DateFromToRangeFilter()
    updated_at = filters.DateFromToRangeFilter()
    signal_type = filters.ChoiceFilter(choices=Signal.SIGNAL_TYPES)
    entry_price = filters.RangeFilter()
    take_profit = filters.RangeFilter()
    stop_loss = filters.RangeFilter()
    is_active = filters.BooleanFilter()
    is_sent = filters.BooleanFilter()
    instrument = filters.CharFilter(field_name='instrument__name', lookup_expr='icontains')
    created_by = filters.NumberFilter(field_name='created_by__id')
    
    class Meta:
        model = Signal
        fields = ['created_at', 'updated_at', 'signal_type', 'entry_price', 
                 'take_profit', 'stop_loss', 'is_active', 'is_sent', 
                 'instrument', 'created_by']

class SubscriptionFilter(filters.FilterSet):
    start_date = filters.DateFromToRangeFilter()
    end_date = filters.DateFromToRangeFilter()
    created_at = filters.DateFromToRangeFilter()
    is_active = filters.BooleanFilter()
    user = filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    plan = filters.CharFilter(field_name='plan__name', lookup_expr='icontains')
    
    class Meta:
        model = Subscription
        fields = ['start_date', 'end_date', 'created_at', 'is_active', 
                 'user', 'plan']

class PaymentFilter(filters.FilterSet):
    created_at = filters.DateFromToRangeFilter()
    updated_at = filters.DateFromToRangeFilter()
    amount = filters.RangeFilter()
    payment_type = filters.ChoiceFilter(choices=Payment.PAYMENT_TYPES)
    status = filters.ChoiceFilter(choices=Payment.STATUS_CHOICES)
    user = filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    subscription_plan = filters.CharFilter(field_name='subscription_plan__name', lookup_expr='icontains')
    
    class Meta:
        model = Payment
        fields = ['created_at', 'updated_at', 'amount', 'payment_type', 
                 'status', 'user', 'subscription_plan']

class ReviewFilter(filters.FilterSet):
    created_at = filters.DateFromToRangeFilter()
    updated_at = filters.DateFromToRangeFilter()
    rating = filters.RangeFilter()
    is_approved = filters.BooleanFilter()
    user = filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    comment = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Review
        fields = ['created_at', 'updated_at', 'rating', 'is_approved', 'user', 'comment']

class InstrumentFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    symbol = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    created_at = filters.DateFromToRangeFilter()
    
    class Meta:
        model = Instrument
        fields = ['name', 'symbol', 'is_active', 'created_at'] 