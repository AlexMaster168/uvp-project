from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'projects'

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'tags', views.TagViewSet, basename='tag')

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('super-structure/', views.SuperStructureView.as_view(), name='super_structure'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('<int:pk>/structure/', views.ProjectStructureView.as_view(), name='structure'),
    path('api/', include(router.urls)),
]
