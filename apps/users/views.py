from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import ListView, CreateView, DetailView, View, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from rest_framework import viewsets
from django.contrib.auth import get_user_model

from .forms import CustomUserCreationForm, AddUserToProjectForm, GlobalSettingsForm, UserProfileForm, CustomLoginForm
from apps.projects.models import ProjectMembership
from .serializers import UserSerializer
from .models import GlobalSettings

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserLoginView(LoginView):
    form_class = CustomLoginForm
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
            else:
                user.is_active = True
                user.save()
        return redirect('users:user_list')


class AddUserToProjectView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = AddUserToProjectForm(request.POST)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.user = user
            if not ProjectMembership.objects.filter(user=user, project=membership.project).exists():
                membership.save()
        return redirect('users:user_detail', pk=pk)


class UpdateUserRoleView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    def post(self, request, pk, membership_id):
        membership = get_object_or_404(ProjectMembership, id=membership_id, user_id=pk)
        new_role = request.POST.get('role')
        if new_role in dict(ProjectMembership.ROLE_CHOICES):
            membership.role = new_role
            membership.save()
        return redirect('users:user_detail', pk=pk)


class RemoveUserFromProjectView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    def post(self, request, pk, membership_id):
        membership = get_object_or_404(ProjectMembership, id=membership_id, user_id=pk)
        membership.delete()
        return redirect('users:user_detail', pk=pk)


class SettingsView(LoginRequiredMixin, SuperUserRequiredMixin, View):
    def get(self, request):
        settings_obj = GlobalSettings.get_settings()
        form = GlobalSettingsForm(instance=settings_obj)
        return render(request, 'users/settings.html', {'form': form})

    def post(self, request):
        settings_obj = GlobalSettings.get_settings()
        form = GlobalSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            return redirect('users:settings')
        return render(request, 'users/settings.html', {'form': form})


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user
