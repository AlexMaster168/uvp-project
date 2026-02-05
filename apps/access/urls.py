from django.urls import path
from . import views

app_name = 'access'

urlpatterns = [
    path('', views.AccessListView.as_view(), name='access_list'),
    path('create/', views.AccessCreateView.as_view(), name='access_create'),
    path('<int:pk>/edit/', views.AccessUpdateView.as_view(), name='access_edit'),
    path('<int:pk>/delete/', views.AccessDeleteView.as_view(), name='access_delete'),
]
