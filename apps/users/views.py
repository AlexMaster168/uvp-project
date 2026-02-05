from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login, logout
from .models import User
from .serializers import UserSerializer, UserCreateSerializer
from .permissions import IsSuperAdminOrAdmin


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_ban'] = self.request.user.is_admin() or self.request.user.is_super_admin()
        return context


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'


class UserBanView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not (request.user.is_admin() or request.user.is_super_admin()):
            return redirect('users:user_list')
        user = get_object_or_404(User, pk=pk)
        if user.status == 'blocked':
            user.unblock()
        else:
            user.block()
        return redirect('users:user_list')


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return Response({'detail': 'Login successful'})
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'detail': 'Logout successful'})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsSuperAdminOrAdmin]

    def get_serializer_class(self):
        if self.action == 'create': return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.query_params.get('q', '')
        if q: queryset = queryset.filter(username__icontains=q) | queryset.filter(email__icontains=q)
        group = self.request.query_params.get('group', '')
        if group: queryset = queryset.filter(u_group__name=group)
        return queryset
