"""Custom permissions for users app."""
from rest_framework import permissions

class IsSuperAdminOrAdmin(permissions.BasePermission):
    """Allow access only to super admins and admins."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_super_admin() or request.user.is_admin()
        )

class IsSuperAdmin(permissions.BasePermission):
    """Allow access only to super admins."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_super_admin()
