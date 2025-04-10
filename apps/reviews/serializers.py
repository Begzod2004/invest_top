from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    updated_admin = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'comment', 'rating', 'is_approved', 
                 'created_at', 'updated_at', 'updated_admin']
        read_only_fields = ['is_approved', 'created_at', 'updated_at', 'updated_admin']

class ReviewAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['is_approved']
