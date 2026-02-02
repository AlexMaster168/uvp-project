from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Tag, Project, ProjectMembership
from .serializers import *
from .permissions import IsProjectMember, IsProjectOwnerOrManager

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    template_name = 'projects/project_form.html'
    fields = ['name', 'description', 'start_date', 'end_date', 'status', 'logo', 'u_tags']
    
    def form_valid(self, form):
        form.instance.u_creator = self.request.user
        response = super().form_valid(form)
        ProjectMembership.objects.create(
            project=self.object,
            user=self.request.user,
            role='owner'
        )
        return response
    
    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = 'projects/project_form.html'
    fields = ['name', 'description', 'start_date', 'end_date', 'status', 'logo', 'u_tags']
    
    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})

# API ViewSets
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'start_date', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProjectCreateUpdateSerializer
        return ProjectDetailSerializer
    
    def perform_create(self, serializer):
        project = serializer.save(u_creator=self.request.user)
        ProjectMembership.objects.create(
            project=project,
            user=self.request.user,
            role='owner'
        )
    
    @action(detail=True, methods=['get', 'post'])
    def structure(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            return Response(project.structure_data)
        elif request.method == 'POST':
            project.structure_data = request.data
            project.save()
            return Response({'status': 'saved'})
