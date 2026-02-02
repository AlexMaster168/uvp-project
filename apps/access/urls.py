from django.urls import path
from . import views

app_name = 'access'

urlpatterns = [
    path('', views.AccessListView.as_view(), name='access_list'),
]
