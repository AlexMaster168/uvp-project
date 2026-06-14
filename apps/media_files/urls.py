from django.urls import path, re_path
from django.conf import settings
from django.views.static import serve
from . import views

app_name = 'media_files'

urlpatterns = [
    path('', views.MediaListView.as_view(), name='media_list'),
    path('create/', views.MediaCreateView.as_view(), name='media_create'),
    path('edit/<int:pk>/', views.MediaUpdateView.as_view(), name='media_edit'),
    path('delete/<int:pk>/', views.MediaDeleteView.as_view(), name='media_delete'),
    re_path(r'^(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
