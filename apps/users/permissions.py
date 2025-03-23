from rest_framework import permissions

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