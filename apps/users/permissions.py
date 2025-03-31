from rest_framework import permissions
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class BasePermission(permissions.BasePermission):
    """
    Base permission class to check if user has required permission
    """
    def has_permission(self, request, view):
        # READ operatsiyalari uchun (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return self.has_read_permission(request, view)
        # WRITE operatsiyalari uchun (POST, PUT, PATCH, DELETE)
        return self.has_write_permission(request, view)
    
    def has_read_permission(self, request, view):
        return True
    
    def has_write_permission(self, request, view):
        return False
    
    def has_permission_or_role(self, user, perm_codename):
        """
        Foydalanuvchida berilgan ruxsat yoki roli borligini tekshirish
        """
        # Admin har doim ruxsat oladi
        if user.is_admin:
            return True
        
        # Guruh orqali ruxsatlarni tekshirish
        if user.groups.filter(permissions__codename=perm_codename).exists():
            return True
        
        # To'g'ridan-to'g'ri ruxsatlarni tekshirish
        if user.user_permissions.filter(codename=perm_codename).exists():
            return True
        
        # Rol orqali ruxsatlarni tekshirish
        if user.roles.filter(permissions__codename=perm_codename).exists():
            return True
        
        return False

class IsAdminOrReadOnly(BasePermission):
    def has_read_permission(self, request, view):
        return True
    
    def has_write_permission(self, request, view):
        return request.user.is_admin

class SignalPermission(BasePermission):
    def has_read_permission(self, request, view):
        return True
    
    def has_write_permission(self, request, view):
        # Admin yoki signal yaratish ruxsati borlar
        if request.user.is_admin or self.has_permission_or_role(request.user, 'can_create_signals'):
            return True
        
        # O'zining signalini tahrirlash/o'chirish
        if view.action in ['update', 'partial_update', 'destroy']:
            signal_id = view.kwargs.get('pk')
            return request.user.signals.filter(id=signal_id).exists()
        
        return False

class UserPermission(BasePermission):
    def has_read_permission(self, request, view):
        # O'zini ma'lumotlari bo'lsa o'qishi mumkin
        if view.action == 'retrieve':
            user_id = view.kwargs.get('pk')
            return str(request.user.id) == str(user_id)
        
        # Admin yoki ruxsati borlar
        return request.user.is_admin or self.has_permission_or_role(request.user, 'can_view_users')
    
    def has_write_permission(self, request, view):
        # Admin yoki ruxsati borlar
        if request.user.is_admin or self.has_permission_or_role(request.user, 'can_edit_users'):
            return True
        
        # O'zining profilini tahrirlash
        if view.action in ['update', 'partial_update']:
            user_id = view.kwargs.get('pk')
            return str(request.user.id) == str(user_id)
        
        return False

class SubscriptionPermission(BasePermission):
    def has_read_permission(self, request, view):
        # Faqat o'z obunalari yoki ruxsati borlar
        if request.user.is_admin or self.has_permission_or_role(request.user, 'can_view_subscriptions'):
            return True
        
        if view.action == 'retrieve':
            subscription_id = view.kwargs.get('pk')
            return request.user.subscriptions.filter(id=subscription_id).exists()
        
        return False
    
    def has_write_permission(self, request, view):
        # Aktivlashtirish/O'chirish uchun admin yoki ruxsati borlar
        return request.user.is_admin or self.has_permission_or_role(request.user, 'can_manage_subscriptions')

class ReviewPermission(BasePermission):
    def has_read_permission(self, request, view):
        # Barcha tasdiqlanganlarni ko'rish, admin o'zgartirilayotganlarni ham
        if request.user.is_admin or self.has_permission_or_role(request.user, 'can_view_reviews'):
            return True
        return Q(is_approved=True)
    
    def has_write_permission(self, request, view):
        # Admin yoki tasdiqlash ruxsati borlar
        return request.user.is_admin or self.has_permission_or_role(request.user, 'can_manage_reviews')

class HasRolePermission(permissions.BasePermission):
    """
    Base permission class to check if user has required permission
    """
    permission_required = None
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_admin:
            return True
            
        return request.user.has_perm(self.permission_required)

class CanViewUsers(HasRolePermission):
    permission_required = 'can_view_users'

class CanEditUsers(HasRolePermission):
    permission_required = 'can_edit_users'

class CanDeleteUsers(HasRolePermission):
    permission_required = 'can_delete_users'

class CanBlockUsers(HasRolePermission):
    permission_required = 'can_block_users'

class CanViewSignals(HasRolePermission):
    permission_required = 'can_view_signals'

class CanCreateSignals(HasRolePermission):
    permission_required = 'can_create_signals'

class CanEditSignals(HasRolePermission):
    permission_required = 'can_edit_signals'

class CanDeleteSignals(HasRolePermission):
    permission_required = 'can_delete_signals'

class CanViewSubscriptions(HasRolePermission):
    permission_required = 'can_view_subscriptions'

class CanManageSubscriptions(HasRolePermission):
    permission_required = 'can_manage_subscriptions'

class CanViewReviews(HasRolePermission):
    permission_required = 'can_view_reviews'

class CanManageReviews(HasRolePermission):
    permission_required = 'can_manage_reviews'

class CanSendBroadcasts(HasRolePermission):
    permission_required = 'can_send_broadcasts'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin

class IsActiveUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active 