from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'status', 'estimated_time', 'actual_time']
    list_filter = ['status', 'project']
    search_fields = ['title']
    filter_horizontal = ['u_users', 'u_tags']
