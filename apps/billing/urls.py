from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.BillingListView.as_view(), name='billing_list'),
    path('create/', views.BillingCreateView.as_view(), name='billing_create'),
    path('<int:pk>/edit/', views.BillingUpdateView.as_view(), name='billing_edit'),
    path('<int:pk>/delete/', views.BillingDeleteView.as_view(), name='billing_delete'),
]
