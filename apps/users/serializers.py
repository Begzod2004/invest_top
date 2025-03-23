from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Role, Permission
from apps.subscriptions.models import Subscription
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']

class PermissionSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer(read_only=True)
    app_label = serializers.CharField(source='content_type.app_label', read_only=True)
    model = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = DjangoPermission
        fields = [
            'id', 'name', 'codename', 
            'content_type', 'app_label', 'model'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ruxsat nomini o'zbekcha qilish
        name = data['name']
        if name.startswith('Can '):
            name = name.replace('Can ', '')
            if name.endswith('s'):
                name = name[:-1]
            data['name'] = name.lower()
        return data

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions']

class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']

class GroupCreateUpdateSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=DjangoPermission.objects.all()
    )
    
    class Meta:
        model = Group
        fields = ['name', 'permissions']

class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    groups = GroupSerializer(many=True, read_only=True)
    user_permissions = PermissionSerializer(many=True, read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'user_id', 'telegram_user_id',
            'first_name', 'last_name', 'phone_number', 'image_url',
            'is_admin', 'is_blocked', 'is_active', 'is_staff',
            'balance', 'date_joined', 'updated_at',
            'roles', 'groups', 'user_permissions', 'full_name'
        ]
        read_only_fields = ['balance', 'date_joined', 'updated_at']

    def get_full_name(self, obj):
        return obj.full_name

    # Subscriptions ni alohida serializer orqali ko'rsatish
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Agar request GET bo'lsa va detail view bo'lsa
        request = self.context.get('request')
        if request and request.method == 'GET' and getattr(request, 'parser_context', {}).get('kwargs', {}).get('pk'):
            try:
                from apps.subscriptions.serializers import SubscriptionSerializer
                subscriptions = instance.subscriptions.all()
                if subscriptions.exists():
                    data['subscriptions'] = SubscriptionSerializer(
                        subscriptions, 
                        many=True, 
                        context={'include_user_details': False}
                    ).data
            except (ImportError, AttributeError):
                pass
        return data

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, required=True)
    password = serializers.CharField(max_length=128, required=True, write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('Foydalanuvchi bloklangan')
                data['user'] = user
            else:
                raise serializers.ValidationError('Username yoki parol noto\'g\'ri')
        else:
            raise serializers.ValidationError('Username va parol kiritilishi shart')
        return data

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'password', 'first_name', 'last_name',
            'phone_number', 'telegram_user_id'
        ]
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'image_url', 'is_blocked'
        ]

