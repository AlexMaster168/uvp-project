from django.urls import path
from . import views

app_name = 'media_files'

urlpatterns = [
    path('create/', views.MediaCreateView.as_view(), name='media_create'),
    path('edit/<int:pk>/', views.MediaUpdateView.as_view(), name='media_edit'),
    path('delete/<int:pk>/', views.MediaDeleteView.as_view(), name='media_delete'),
]
