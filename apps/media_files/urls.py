from django.urls import path
from . import views

app_name = 'media_files'

urlpatterns = [
    path('', views.MediaFileListView.as_view(), name='media_list'),
]
