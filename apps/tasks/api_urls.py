from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='tasks')
router.register(r'subtasks', views.SubTaskViewSet, basename='subtasks')

urlpatterns = [
    path('', include(router.urls)),
]
