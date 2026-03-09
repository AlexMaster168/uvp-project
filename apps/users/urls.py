from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_urls import router

app_name = 'users'

urlpatterns = [
    path('api/', include(router.urls)),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('', views.UserListView.as_view(), name='user_list'),
    path('create/', views.UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('<int:pk>/block/', views.UserToggleBlockView.as_view(), name='user_toggle_block'),
    path('<int:pk>/projects/add/', views.AddUserToProjectView.as_view(), name='user_add_project'),
    path('<int:pk>/projects/<int:membership_id>/update/', views.UpdateUserRoleView.as_view(), name='user_update_role'),
    path('<int:pk>/projects/<int:membership_id>/remove/', views.RemoveUserFromProjectView.as_view(),
         name='user_remove_project'),
]
