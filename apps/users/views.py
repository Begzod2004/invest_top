import hashlib
import hmac
import json
import time
import asyncio
from django.conf import settings
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.serializers import Serializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
from apps.users.models import User, Role, Permission
from apps.users.serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    RoleSerializer, PermissionSerializer, LoginSerializer,
    GroupSerializer, GroupCreateUpdateSerializer
)
from apps.invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot
from rest_framework import viewsets
from .permissions import IsAdmin, IsActiveUser
from django.contrib.auth.models import Group, Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

@extend_schema(
    tags=['auth'],
    request=Serializer,
    responses={200: UserSerializer}
)
class TelegramAuthView(APIView):
    """
    Telegram orqali autentifikatsiya
    """
    serializer_class = Serializer

    def post(self, request):
        telegram_data = request.data

        # 1️⃣ Telegramdan kelgan ma'lumotni tekshiramiz
        auth_data = telegram_data.get("auth_data")
        if not auth_data:
            return Response({"error": "No authentication data provided"}, status=400)

        # 2️⃣ HMAC (sha256) orqali Telegram imzosi to'g'riligini tekshiramiz
        bot_token = settings.BOT_TOKEN.encode("utf-8")
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(json.loads(auth_data).items()) if k != "hash"
        ).encode("utf-8")

        secret_key = hashlib.sha256(bot_token).digest()
        computed_hash = hmac.new(secret_key, data_check_string, hashlib.sha256).hexdigest()

        if computed_hash != json.loads(auth_data)["hash"]:
            return Response({"error": "Invalid authentication data"}, status=400)

        # 3️⃣ Foydalanuvchini bazada qidiramiz yoki yaratamiz
        telegram_id = json.loads(auth_data)["id"]
        first_name = json.loads(auth_data).get("first_name", "")
        last_name = json.loads(auth_data).get("last_name", "")
        username = json.loads(auth_data).get("username", "")

        user, created = User.objects.get_or_create(
            telegram_user_id=telegram_id,
            defaults={"first_name": first_name, "last_name": last_name, "user_id": telegram_id, "created_at": now()},
        )

        # 4️⃣ Foydalanuvchiga JWT token yaratamiz
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "Authentication successful",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {
                    "id": user.id,
                    "telegram_id": user.telegram_user_id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": username,
                },
            }
        )

@extend_schema(
    tags=['users'],
    request=Serializer,
    parameters=[
        OpenApiParameter(
            name='user_id',
            type=int,
            location=OpenApiParameter.PATH,
            description='Foydalanuvchi ID si'
        ),
        OpenApiParameter(
            name='message',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Yuborish uchun xabar'
        ),
    ]
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_message_to_user(request, user_id):
    """Foydalanuvchiga xabar yuborish"""
    try:
        user = get_object_or_404(User, id=user_id)
        message = request.data.get('message')
        
        if not message:
            return Response({
                'status': 'error',
                'message': 'Xabar matni kiritilmagan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Xabarni yuborish
        async def send_message():
            bot = Bot(token=BOT_TOKEN)
            try:
                await bot.send_message(
                    chat_id=int(user.telegram_user_id),
                    text=message
                )
                success = True
            except Exception as e:
                success = False
                error = str(e)
            
            await bot.session.close()
            return success, error if 'error' in locals() else None
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success, error = loop.run_until_complete(send_message())
        loop.close()
        
        if success:
            return Response({
                'status': 'success',
                'message': f'Xabar {user.first_name} ga muvaffaqiyatli yuborildi'
            })
        else:
            return Response({
                'status': 'error',
                'message': f'Xabarni {user.first_name} ga yuborishda xatolik: {error}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['auth'],
    request=LoginSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'access_token': {'type': 'string'},
                'refresh_token': {'type': 'string'},
                'user': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'string'},
                        'username': {'type': 'string'},
                        'first_name': {'type': 'string'},
                        'last_name': {'type': 'string'},
                        'is_admin': {'type': 'boolean'},
                    }
                }
            }
        }
    }
)
class LoginView(APIView):
    """
    Login qilish uchun API
    
    Username va password orqali tizimga kirish.
    Muvaffaqiyatli bo'lsa access va refresh tokenlarni qaytaradi.
    """
    permission_classes = []
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': str(user.id),
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_admin': user.is_admin,
            }
        })

@extend_schema_view(
    list=extend_schema(
        tags=['users'],
        summary="Foydalanuvchilar ro'yxati",
        description="Barcha foydalanuvchilarni ko'rish"
    ),
    create=extend_schema(
        tags=['users-admin'],
        summary="Yangi foydalanuvchi yaratish",
        description="Admin uchun yangi foydalanuvchi yaratish"
    ),
    retrieve=extend_schema(
        tags=['users'],
        summary="Foydalanuvchi ma'lumotlari",
        description="Foydalanuvchi haqida to'liq ma'lumot"
    ),
    update=extend_schema(
        tags=['users-admin'],
        summary="Foydalanuvchini yangilash",
        description="Admin uchun foydalanuvchi ma'lumotlarini yangilash"
    )
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def block_user(self, request, pk=None):
        user = self.get_object()
        user.is_blocked = True
        user.save()
        return Response({'status': 'user blocked'})

    @action(detail=True, methods=['post'])
    def unblock_user(self, request, pk=None):
        user = self.get_object()
        user.is_blocked = False
        user.save()
        return Response({'status': 'user unblocked'})

    @extend_schema(
        tags=['users-admin'],
        summary="Foydalanuvchini guruhlarga qo'shish",
        description="Foydalanuvchini berilgan guruhlarga qo'shish",
        request={
            'type': 'object',
            'properties': {
                'groups': {
                    'type': 'array',
                    'items': {'type': 'integer'},
                    'description': 'Guruh IDlari'
                }
            },
            'required': ['groups']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'added_groups': {'type': 'array', 'items': {'type': 'string'}}
                }
            },
            400: {'description': 'Noto\'g\'ri so\'rov'},
            404: {'description': 'Guruh topilmadi'}
        }
    )
    @action(detail=True, methods=['post'])
    def add_to_groups(self, request, pk=None):
        """Foydalanuvchini guruhlarga qo'shish"""
        user = self.get_object()
        
        # Request body validatsiyasi
        groups_ids = request.data.get('groups')
        if not groups_ids or not isinstance(groups_ids, list):
            return Response(
                {'error': 'groups maydonida guruh IDlari ro\'yxati bo\'lishi kerak'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Guruhlarni bazadan olish
        groups = Group.objects.filter(id__in=groups_ids)
        if not groups.exists():
            return Response(
                {'error': 'Berilgan IDga ega guruhlar topilmadi'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Foydalanuvchini guruhlarga qo'shish
        user.groups.add(*groups)
        
        return Response({
            'status': 'groups added',
            'added_groups': list(groups.values_list('name', flat=True))
        })

    @action(detail=True, methods=['post'])
    def remove_from_groups(self, request, pk=None):
        user = self.get_object()
        groups = Group.objects.filter(id__in=request.data.get('groups', []))
        user.groups.remove(*groups)
        return Response({'status': 'groups removed'})

    @action(detail=True, methods=['post'])
    def add_permissions(self, request, pk=None):
        user = self.get_object()
        permissions = Permission.objects.filter(id__in=request.data.get('permissions', []))
        user.user_permissions.add(*permissions)
        return Response({'status': 'permissions added'})

    @action(detail=True, methods=['post'])
    def remove_permissions(self, request, pk=None):
        user = self.get_object()
        permissions = Permission.objects.filter(id__in=request.data.get('permissions', []))
        user.user_permissions.remove(*permissions)
        return Response({'status': 'permissions removed'})

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Ruxsatlarni ko'rish uchun API
    """
    serializer_class = PermissionSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        # Django Permission modelini ishlatamiz
        queryset = DjangoPermission.objects.select_related('content_type').all()
        
        # App bo'yicha filtrlash
        app_label = self.request.query_params.get('app', None)
        if app_label:
            queryset = queryset.filter(content_type__app_label=app_label)
            
        # Model bo'yicha filtrlash
        model = self.request.query_params.get('model', None)
        if model:
            queryset = queryset.filter(content_type__model=model)
            
        return queryset.order_by('content_type__app_label', 'codename')

    @action(detail=False, methods=['get'])
    def apps(self, request):
        """Mavjud app'lar ro'yxatini qaytaradi"""
        apps = ContentType.objects.values_list(
            'app_label', flat=True
        ).distinct().order_by('app_label')
        return Response(list(apps))

    @action(detail=False, methods=['get'])
    def models(self, request):
        """App ichidagi modellar ro'yxatini qaytaradi"""
        app_label = request.query_params.get('app')
        if not app_label:
            return Response({"error": "app parameter is required"}, status=400)
            
        models = ContentType.objects.filter(
            app_label=app_label
        ).values_list('model', flat=True).order_by('model')
        return Response(list(models))

class GroupViewSet(viewsets.ModelViewSet):
    """
    Guruhlarni boshqarish uchun API
    """
    queryset = Group.objects.all()
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GroupCreateUpdateSerializer
        return GroupSerializer

    @action(detail=True, methods=['post'])
    def add_permissions(self, request, pk=None):
        group = self.get_object()
        permissions = Permission.objects.filter(id__in=request.data.get('permissions', []))
        group.permissions.add(*permissions)
        return Response({'status': 'permissions added'})

    @action(detail=True, methods=['post'])
    def remove_permissions(self, request, pk=None):
        group = self.get_object()
        permissions = Permission.objects.filter(id__in=request.data.get('permissions', []))
        group.permissions.remove(*permissions)
        return Response({'status': 'permissions removed'})

@extend_schema(
    tags=['auth'],
    responses={200: UserSerializer}
)
class VerifyMeView(APIView):
    """
    Joriy foydalanuvchi ma'lumotlarini olish
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        data = serializer.data

        # Foydalanuvchi ruxsatlarini qo'shamiz
        permissions = []
        # Django permissions
        for perm in user.user_permissions.all():
            permissions.append(f"{perm.content_type.app_label}.{perm.codename}")
        # Group permissions
        for group in user.groups.all():
            for perm in group.permissions.all():
                permissions.append(f"{perm.content_type.app_label}.{perm.codename}")

        data['permissions'] = list(set(permissions))  # dublikatlarni olib tashlaymiz
        
        return Response(data)

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Token olish uchun view
    
    Username va password orqali access va refresh tokenlarni olish
    """
    @extend_schema(
        tags=['auth'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string'},
                    'refresh': {'type': 'string'},
                    'user': {'type': 'object'}
                }
            }
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Token ma'lumotlariga user ma'lumotlarini qo'shamiz
        if response.status_code == 200:
            access_token = response.data.get('access')
            if access_token:
                # Tokendan user IDsini olamiz
                decoded_token = AccessToken(access_token)
                user_id = decoded_token['user_id']
                
                # User ma'lumotlarini olamiz
                user = User.objects.get(id=user_id)
                user_data = UserSerializer(user).data
                
                # Ruxsatlarni qo'shamiz
                permissions = []
                for perm in user.user_permissions.all():
                    permissions.append(f"{perm.content_type.app_label}.{perm.codename}")
                for group in user.groups.all():
                    for perm in group.permissions.all():
                        permissions.append(f"{perm.content_type.app_label}.{perm.codename}")
                
                user_data['permissions'] = list(set(permissions))
                
                response.data['user'] = user_data
        
        return response

@extend_schema(
    tags=['auth'],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'permissions': {
                    'type': 'array',
                    'items': {'type': 'string'}
                },
                'is_admin': {'type': 'boolean'},
                'menu_items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'title': {'type': 'string'},
                            'path': {'type': 'string'},
                            'icon': {'type': 'string'},
                            'permissions': {'type': 'array', 'items': {'type': 'string'}}
                        }
                    }
                }
            }
        }
    }
)
class UserPermissionsView(APIView):
    """
    Foydalanuvchining ruxsatlari va menu elementlarini qaytaradi.
    Frontend uchun sidebar va permission checking qilish uchun ishlatiladi.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        # Barcha ruxsatlarni yig'ish
        permissions = self.get_all_permissions(user)
        
        # Menu itemlarni olish
        menu_items = self.get_menu_items(permissions, user.is_admin)
        
        return Response({
            'permissions': permissions,
            'is_admin': user.is_admin,
            'menu_items': menu_items,
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name
            }
        })
    
    def get_all_permissions(self, user):
        """
        User permissions, group permissions va role permissions larni birlashtiradi
        """
        all_permissions = set()
        
        # Django standart permission tizimi
        for perm in user.user_permissions.all().values_list('codename', flat=True):
            all_permissions.add(perm)
        
        # Group permissions
        for group in user.groups.all():
            for perm in group.permissions.all().values_list('codename', flat=True):
                all_permissions.add(perm)
        
        # Custom role tizimi
        for role in user.roles.all():
            for perm in role.permissions.all().values_list('codename', flat=True):
                all_permissions.add(perm)
        
        return list(all_permissions)
    
    def get_menu_items(self, permissions, is_admin):
        """Menu elementlarini qaytaradi"""
        # Menu strukturasi
        menu_items = [
            {
                'id': 'dashboard',
                'title': 'Dashboard',
                'icon': 'dashboard',
                'path': '/dashboard',
                'permissions': []  # Bo'sh permissions = hammaga ko'rinadi
            }
        ]
        
        # Signals menu
        if is_admin or 'can_view_signals' in permissions:
            signals_item = {
                'id': 'signals',
                'title': 'Signallar',
                'icon': 'chart-line',
                'path': '/signals',
                'permissions': ['can_view_signals']
            }
            
            # Submenu for admins or users with create permission
            if is_admin or 'can_create_signals' in permissions:
                signals_item['children'] = [
                    {
                        'id': 'create-signal',
                        'title': 'Yangi signal',
                        'path': '/signals/create',
                        'permissions': ['can_create_signals']
                    }
                ]
            
            menu_items.append(signals_item)
        
        # Users menu (faqat adminlar va ruxsati borlar uchun)
        if is_admin or 'can_view_users' in permissions:
            users_item = {
                'id': 'users',
                'title': 'Foydalanuvchilar',
                'icon': 'users',
                'path': '/users',
                'permissions': ['can_view_users']
            }
            menu_items.append(users_item)
        
        # To'lovlar menu
        if is_admin or 'can_view_payments' in permissions:
            payments_item = {
                'id': 'payments',
                'title': 'To\'lovlar',
                'icon': 'credit-card',
                'path': '/payments',
                'permissions': ['can_view_payments']
            }
            menu_items.append(payments_item)
        
        # Obunalar menu
        if is_admin or 'can_view_subscriptions' in permissions:
            subscriptions_item = {
                'id': 'subscriptions',
                'title': 'Obunalar',
                'icon': 'star',
                'path': '/subscriptions',
                'permissions': ['can_view_subscriptions']
            }
            menu_items.append(subscriptions_item)
        
        # Instrumentlar menu
        instruments_item = {
            'id': 'instruments',
            'title': 'Instrumentlar',
            'icon': 'chart-bar',
            'path': '/instruments',
            'permissions': []  # Hamma uchun
        }
        menu_items.append(instruments_item)
        
        # Sharhlar menu
        if is_admin or 'can_view_reviews' in permissions:
            reviews_item = {
                'id': 'reviews',
                'title': 'Sharhlar',
                'icon': 'comment',
                'path': '/reviews',
                'permissions': ['can_view_reviews']
            }
            menu_items.append(reviews_item)
        
        # Admin sozlamalari (faqat admin uchun)
        if is_admin:
            settings_item = {
                'id': 'settings',
                'title': 'Sozlamalar',
                'icon': 'cog',
                'path': '/settings',
                'permissions': ['is_admin']
            }
            menu_items.append(settings_item)
        
        return menu_items
