from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'tasks'

router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='tasks')
router.register(r'subtasks', views.SubTaskViewSet, basename='subtasks')

urlpatterns = [
    path('', views.TaskListView.as_view(), name='task_list'),
    path('create/', views.TaskCreateView.as_view(), name='task_create'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
]
