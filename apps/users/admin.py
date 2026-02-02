"""Admin for users app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, GroupUsers

@admin.register(GroupUsers)
class GroupUsersAdmin(admin.ModelAdmin):
    list_display = ['name']
    
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'u_group', 'status', 'is_staff']
    list_filter = ['u_group', 'status', 'is_staff', 'is_superuser']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('u_group', 'status')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительно', {'fields': ('email', 'u_group', 'status')}),
    )
