from django.contrib import admin
from .models import MediaFile

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'project', 'uploaded_at']
    list_filter = ['uploaded_at', 'project']
    search_fields = ['file', 'description']
