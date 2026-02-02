"""URL Configuration for УВП project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Redirect root to projects
    path('', RedirectView.as_view(url='/projects/', permanent=False)),
    
    # Auth
    path('', include('apps.users.urls')),
    
    # Apps
    path('projects/', include('apps.projects.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('billing/', include('apps.billing.urls')),
    path('access/', include('apps.access.urls')),
    path('media-files/', include('apps.media_files.urls')),
    
    # API
    path('api/', include('apps.users.api_urls')),
    path('api/', include('apps.projects.api_urls')),
    path('api/', include('apps.tasks.api_urls')),
    path('api/', include('apps.billing.api_urls')),
    path('api/', include('apps.access.api_urls')),
    path('api/', include('apps.media_files.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin customization
admin.site.site_header = 'УВП Администрирование'
admin.site.site_title = 'УВП Admin'
admin.site.index_title = 'Добро пожаловать в панель управления УВП'
