from rest_framework import permissions

class BasePermission(permissions.BasePermission):
    """Base permission class for all custom permissions"""
    def has_permission(self, request, view):
        # READ operatsiyalari uchun (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return self.has_read_permission(request, view)
        # WRITE operatsiyalari uchun (POST, PUT, PATCH, DELETE)
        return self.has_write_permission(request, view)
    
    def has_read_permission(self, request, view):
        """Override this method for read permissions"""
        return True
    
    def has_write_permission(self, request, view):
        """Override this method for write permissions"""
        return False
    
    def has_permission_or_role(self, user, perm_codename):
        """User permission yoki role bor-yo'qligini tekshirish"""
        # Agar admin bo'lsa
        if user.is_superuser or user.is_admin:
            return True
            
        # Django standard permissions
        if user.has_perm(perm_codename):
            return True
        
        # Custom roles permissions
        for role in user.roles.all():
            if role.permissions.filter(codename=perm_codename).exists():
                return True
        
        # User groups permissions
        for group in user.groups.all():
            if group.permissions.filter(codename=perm_codename).exists():
                return True
        
        return False

class IsAdminOrReadOnly(BasePermission):
    """Admin yoki faqat o'qish"""
    def has_read_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_write_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin

class SignalPermission(BasePermission):
    """Signal uchun ruxsatlar"""
    def has_read_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_write_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_admin:
            return True
            
        # Custom logika
        if request.method == 'POST':
            return self.has_permission_or_role(request.user, 'can_create_signals')
        elif request.method in ['PUT', 'PATCH']:
            return self.has_permission_or_role(request.user, 'can_edit_signals')
        elif request.method == 'DELETE':
            return self.has_permission_or_role(request.user, 'can_delete_signals')
        
        return False

class UserPermission(BasePermission):
    """User uchun ruxsatlar"""
    def has_read_permission(self, request, view):
        # O'zini ma'lumotlari bo'lsa o'qishi mumkin
        if view.action == 'retrieve' and str(request.user.id) == view.kwargs.get('pk'):
            return True
        
        # List ko'rish uchun can_view_users kerak
        return self.has_permission_or_role(request.user, 'can_view_users')
    
    def has_write_permission(self, request, view):
        # Admin yoki ruxsati borlar
        if request.user.is_admin:
            return True
            
        # O'zini ma'lumotlarini o'zgartirishi mumkin
        if view.action in ['update', 'partial_update'] and str(request.user.id) == view.kwargs.get('pk'):
            return True
            
        # Foydalanuvchilarni boshqarish uchun
        if view.action == 'create':
            return self.has_permission_or_role(request.user, 'can_create_users')
        elif view.action in ['update', 'partial_update']:
            return self.has_permission_or_role(request.user, 'can_edit_users')
        elif view.action == 'destroy':
            return self.has_permission_or_role(request.user, 'can_delete_users')
        
        return False

class PaymentPermission(BasePermission):
    """To'lovlar uchun ruxsatlar"""
    def has_read_permission(self, request, view):
        # Faqat o'z to'lovlari yoki ruxsati borlar
        if not request.user.is_authenticated:
            return False
            
        # Admin yoki can_view_payments ruxsati borlar
        if request.user.is_admin or self.has_permission_or_role(request.user, 'can_view_payments'):
            return True
            
        # O'z to'lovlarini ko'rish
        if view.action == 'list':
            # UserFilter bilan cheklangan (view.py da filter_queryset orqali)
            return True
        
        # Detail ko'rish uchun o'zining to'lovi bo'lishi kerak
        if view.action == 'retrieve':
            payment_id = view.kwargs.get('pk')
            return request.user.payments.filter(id=payment_id).exists()
        
        return False
    
    def has_write_permission(self, request, view):
        # Approve/Reject uchun admin yoki ruxsati borlar
        if view.action == 'approve':
            return self.has_permission_or_role(request.user, 'can_approve_payments')
        elif view.action == 'reject':
            return self.has_permission_or_role(request.user, 'can_reject_payments')
        
        # Create uchun faqat authenticated user
        if view.action == 'create':
            return request.user.is_authenticated
        
        # Delete/Update uchun admin yoki o'zi (pending holatda)
        if view.action in ['update', 'partial_update', 'destroy']:
            if request.user.is_admin:
                return True
            
            payment_id = view.kwargs.get('pk')
            # Faqat o'zining pending to'lovini o'zgartirish/o'chirish mumkin
            return request.user.payments.filter(id=payment_id, status='PENDING').exists()
        
        return False

class SubscriptionPermission(BasePermission):
    """Obunalar uchun ruxsatlar"""
    def has_read_permission(self, request, view):
        # Faqat o'z obunalari yoki ruxsati borlar
        if not request.user.is_authenticated:
            return False
            
        # Admin yoki can_view_subscriptions ruxsati borlar
        if request.user.is_admin or self.has_permission_or_role(request.user, 'can_view_subscriptions'):
            return True
            
        # O'z obunalarini ko'rish
        if view.action == 'list':
            # UserFilter bilan cheklangan (view.py da filter_queryset orqali)
            return True
        
        # Detail ko'rish uchun o'zining obunasi bo'lishi kerak
        if view.action == 'retrieve':
            subscription_id = view.kwargs.get('pk')
            return request.user.subscriptions.filter(id=subscription_id).exists()
        
        return False
    
    def has_write_permission(self, request, view):
        # Aktivlashtirish/O'chirish uchun admin yoki ruxsati borlar
        if view.action in ['activate_subscription', 'deactivate_subscription']:
            return request.user.is_admin or self.has_permission_or_role(request.user, 'can_manage_subscriptions')
        
        # Create/Update/Delete uchun admin
        return request.user.is_admin

class ReviewPermission(BasePermission):
    """Sharhlar uchun ruxsatlar"""
    def has_read_permission(self, request, view):
        # Barcha tasdiqlanganlarni ko'rish, admin o'zgartirilayotganlarni ham
        if request.user.is_admin or self.has_permission_or_role(request.user, 'can_view_reviews'):
            return True
            
        # Oddiy foydalanuvchilar faqat tasdiqlangan sharhlarni ko'radi
        return request.user.is_authenticated
    
    def has_write_permission(self, request, view):
        # Admin yoki tasdiqlash ruxsati borlar
        if view.action in ['update', 'partial_update', 'destroy'] or request.query_params.get('action') == 'approve':
            return request.user.is_admin or self.has_permission_or_role(request.user, 'can_manage_reviews')
        
        # Har qanday authenticated user create qilishi mumkin
        if view.action == 'create':
            return request.user.is_authenticated
        
        return False

# Legacy permissions (Eski kod bilan moslik uchun)
class HasRolePermission(permissions.BasePermission):
    """
    Base permission class to check if user has required permission
    """
    permission_required = None

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if not request.user.is_authenticated:
            return False
        return request.user.has_permission(self.permission_required)

# Foydalanuvchilar uchun permission classlar
class CanViewUsers(HasRolePermission):
    permission_required = 'can_view_users'

class CanEditUsers(HasRolePermission):
    permission_required = 'can_edit_users'

class CanDeleteUsers(HasRolePermission):
    permission_required = 'can_delete_users'

class CanBlockUsers(HasRolePermission):
    permission_required = 'can_block_users'

# Signallar uchun permission classlar
class CanViewSignals(HasRolePermission):
    permission_required = 'can_view_signals'

class CanCreateSignals(HasRolePermission):
    permission_required = 'can_create_signals'

class CanEditSignals(HasRolePermission):
    permission_required = 'can_edit_signals'

class CanDeleteSignals(HasRolePermission):
    permission_required = 'can_delete_signals'

# Obunalar uchun permission classlar
class CanViewSubscriptions(HasRolePermission):
    permission_required = 'can_view_subscriptions'

class CanManageSubscriptions(HasRolePermission):
    permission_required = 'can_manage_subscriptions'

# To'lovlar uchun permission classlar
class CanViewPayments(HasRolePermission):
    permission_required = 'can_view_payments'

class CanApprovePayments(HasRolePermission):
    permission_required = 'can_approve_payments'

class CanRejectPayments(HasRolePermission):
    permission_required = 'can_reject_payments'

# Sharhlar uchun permission classlar
class CanViewReviews(HasRolePermission):
    permission_required = 'can_view_reviews'

class CanManageReviews(HasRolePermission):
    permission_required = 'can_manage_reviews'

# Xabarlar uchun permission class
class CanSendBroadcasts(HasRolePermission):
    permission_required = 'can_send_broadcasts'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_admin

class IsActiveUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_active and not request.user.is_blocked 