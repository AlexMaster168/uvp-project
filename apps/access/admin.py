from django.contrib import admin
from .models import Access

@admin.register(Access)
class AccessAdmin(admin.ModelAdmin):
    list_display = ['project', 'login', 'url']
    list_filter = ['tags', 'registration_date']
    search_fields = ['login', 'url', 'description']
