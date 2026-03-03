from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('users/', include('apps.users.urls', namespace='users')),
    path('projects/', include('apps.projects.urls', namespace='projects')),
    path('tasks/', include('apps.tasks.urls', namespace='tasks')),
    path('billing/', include('apps.billing.urls', namespace='billing')),
    path('access/', include('apps.access.urls', namespace='access')),
    path('media/', include('apps.media_files.urls', namespace='media_files')),

    path('api/users/', include('apps.users.api_urls')),
    path('api/projects/', include('apps.projects.api_urls')),
    path('api/tasks/', include('apps.tasks.api_urls')),
    path('api/billing/', include('apps.billing.api_urls')),
    path('api/access/', include('apps.access.api_urls')),
    path('api/media/', include('apps.media_files.api_urls')),

    path('', include('apps.projects.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
