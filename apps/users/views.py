from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import ListView, CreateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from rest_framework import viewsets
from django.contrib.auth import get_user_model

from .forms import CustomUserCreationForm, AddUserToProjectForm
from apps.projects.models import ProjectMembership
from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.request.GET.get('next') or '/'


class UserLogoutView(LogoutView):
    next_page = '/users/login/'


class SuperUserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class UserListView(LoginRequiredMixin, SuperUserRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    ordering = ['id']


class UserCreateView(LoginRequiredMixin, SuperUserRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'

    def get_success_url(self):
        return reverse('users:user_detail', kwargs={'pk': self.object.pk})


class UserDetailView(LoginRequiredMixin, SuperUserRequiredMixin, DetailView):
    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['add_project_form'] = AddUserToProjectForm()
        context['memberships'] = ProjectMembership.objects.filter(user=self.object)
        return context


class UserToggleBlockView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user != request.user:
            if user.is_active:
                user.is_active = False
                user.save()
                status = "заблокирован"
            else:
                user.is_active = True
                user.save()
                status = "разблокирован"

            messages.success(request, f"Пользователь {user.username} {status}.")
        else:
            messages.error(request, "Нельзя заблокировать самого себя.")
        return redirect('users:user_list')


class AddUserToProjectView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = AddUserToProjectForm(request.POST)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.user = user

            if ProjectMembership.objects.filter(user=user, project=membership.project).exists():
                messages.warning(request, "Пользователь уже в этом проекте.")
            else:
                membership.save()
                messages.success(request, "Пользователь добавлен в проект.")
        else:
            messages.error(request, "Ошибка при добавлении.")
        return redirect('users:user_detail', pk=pk)


class UpdateUserRoleView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    def post(self, request, pk, membership_id):
        membership = get_object_or_404(ProjectMembership, id=membership_id, user_id=pk)
        new_role = request.POST.get('role')
        if new_role in dict(ProjectMembership.ROLE_CHOICES):
            membership.role = new_role
            membership.save()
            messages.success(request, "Роль обновлена.")
        else:
            messages.error(request, "Некорректная роль.")
        return redirect('users:user_detail', pk=pk)
