from django.contrib import admin
from .models import Tag, Project, ProjectMembership, Plan

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'importance', 'range']
    search_fields = ['name']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'u_creator', 'start_date', 'end_date']
    list_filter = ['status', 'start_date']
    search_fields = ['name', 'description']
    filter_horizontal = ['u_tags']

class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1

@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'role']
    list_filter = ['role']
    
@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['u_project', 'u_task', 'order_index']
