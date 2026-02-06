from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.projects.urls')),
    path('users/', include('apps.users.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('access/', include('apps.access.urls')),
    path('billing/', include('apps.billing.urls')),
    path('media-files/', include('apps.media_files.urls')),

    path('api/', include('apps.projects.api_urls')),
    path('api/', include('apps.tasks.api_urls')),
    path('api/', include('apps.billing.api_urls')),
    path('api/', include('apps.users.api_urls')),
    path('api/', include('apps.media_files.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
