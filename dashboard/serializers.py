from rest_framework import serializers
from .models import BroadcastMessage
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        ref_name = 'DashboardUserSerializer'

class BroadcastMessageSerializer(serializers.ModelSerializer):
    sent_by = UserSerializer(read_only=True)
    
    class Meta:
        model = BroadcastMessage
        fields = '__all__'
        read_only_fields = ['success_count', 'error_count', 'sent_by', 'created_at'] 