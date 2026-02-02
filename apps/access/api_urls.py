from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'access', views.AccessViewSet, basename='access')

urlpatterns = [
    path('', include(router.urls)),
]
