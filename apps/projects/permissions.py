from rest_framework import permissions
from .models import ProjectMembership

class IsProjectMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_super_admin():
            return True
        try:
            membership = ProjectMembership.objects.get(
                project=obj if hasattr(obj, 'members') else obj.project,
                user=request.user
            )
            return True
        except ProjectMembership.DoesNotExist:
            return False

class IsProjectOwnerOrManager(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_super_admin():
            return True
        try:
            membership = ProjectMembership.objects.get(
                project=obj if hasattr(obj, 'members') else obj.project,
                user=request.user
            )
            return membership.role in ['owner', 'manager']
        except ProjectMembership.DoesNotExist:
            return False
