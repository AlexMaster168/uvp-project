from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.BillingListView.as_view(), name='billing_list'),
]
