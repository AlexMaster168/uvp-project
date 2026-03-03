from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('', views.UserListView.as_view(), name='user_list'),
    path('create/', views.UserCreateView.as_view(), name='user_create'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('<int:pk>/toggle_block/', views.UserToggleBlockView.as_view(), name='user_toggle_block'),
    path('<int:pk>/add_project/', views.AddUserToProjectView.as_view(), name='user_add_project'),
    path('<int:pk>/update_role/<int:membership_id>/', views.UpdateUserRoleView.as_view(), name='user_update_role'),
    path('<int:pk>/remove_project/<int:membership_id>/', views.RemoveUserFromProjectView.as_view(),
         name='user_remove_project'),
]
