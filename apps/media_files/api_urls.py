from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'media', views.MediaFileViewSet, basename='media')

urlpatterns = [
    path('', include(router.urls)),
]
