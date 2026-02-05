from django.urls import path
from . import views

app_name = 'media_files'

urlpatterns = [
    path('', views.MediaFileListView.as_view(), name='media_list'),
    path('upload/', views.MediaFileCreateView.as_view(), name='media_create'),
    path('<int:pk>/delete/', views.MediaFileDeleteView.as_view(), name='media_delete'),
]
