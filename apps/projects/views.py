import json
from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .forms import ProjectForm
from .models import Tag, Project, ProjectMembership
from .serializers import *
from apps.tasks.models import Task
from apps.access.models import Access
from apps.billing.models import Billing


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        status_val = self.request.GET.get('status')

        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(u_tags__name__icontains=q)
            ).distinct()

        if status_val:
            qs = qs.filter(status=status_val)

        return qs


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'


class ProjectStructureView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/structure.html'
    context_object_name = 'project'


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def form_valid(self, form):
        form.instance.u_creator = self.request.user
        response = super().form_valid(form)
        ProjectMembership.objects.create(project=self.object, user=self.request.user, role='owner')
        return response

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:project_list')


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
        ProjectMembership.objects.create(project=project, user=self.request.user, role='owner')

    @action(detail=True, methods=['get', 'post'])
    def structure(self, request, pk=None):
        project = self.get_object()

        if request.method == 'GET':
            structure = project.structure_data or {'nodes': [], 'connections': []}
            if isinstance(structure, str):
                structure = json.loads(structure)

            nodes = structure.get('nodes', [])
            connections = structure.get('connections', [])

            existing_ids = {
                (n.get('type'), n.get('data', {}).get('db_id')): n
                for n in nodes
                if n.get('data', {}).get('db_id')
            }

            db_tasks = Task.objects.filter(project=project)
            for task in db_tasks:
                if ('task', task.id) not in existing_ids:
                    nodes.append({
                        "id": f"task_{task.id}",
                        "type": "task",
                        "title": task.title,
                        "status": task.status,
                        "x": 100,
                        "y": 100 + len(nodes) * 50,
                        "data": {"db_id": task.id, "title": task.title}
                    })
                else:
                    node = existing_ids[('task', task.id)]
                    node['title'] = task.title
                    node['status'] = task.status
                    node['data']['title'] = task.title

            db_accesses = Access.objects.filter(project=project)
            for acc in db_accesses:
                if ('access', acc.id) not in existing_ids:
                    nodes.append({
                        "id": f"access_{acc.id}",
                        "type": "access",
                        "title": acc.url or acc.description or "Access",
                        "status": "active",
                        "x": 400,
                        "y": 100 + len(nodes) * 50,
                        "data": {"db_id": acc.id, "login": acc.login}
                    })

            db_billings = Billing.objects.filter(project=project)
            for bill in db_billings:
                if ('billing', bill.id) not in existing_ids:
                    nodes.append({
                        "id": f"billing_{bill.id}",
                        "type": "billing",
                        "title": f"{bill.amount} ({bill.get_operation_display()})",
                        "status": bill.operation,
                        "x": 700,
                        "y": 100 + len(nodes) * 50,
                        "data": {"db_id": bill.id, "amount": str(bill.amount)}
                    })

            return Response({"nodes": nodes, "connections": connections})

        elif request.method == 'POST':
            data = request.data
            nodes = data.get('nodes', [])

            for node_data in nodes:
                node_type = node_data.get('type')
                db_id = node_data.get('data', {}).get('db_id')

                if node_type == 'task':
                    title = node_data.get('data', {}).get('title', 'New Task')
                    status_val = node_data.get('status', 'todo')

                    if db_id:
                        Task.objects.filter(pk=db_id, project=project).update(title=title, status=status_val)
                    else:
                        task = Task.objects.create(project=project, title=title, status=status_val)
                        node_data['data']['db_id'] = task.id
                        node_data['id'] = f"task_{task.id}"

                elif node_type == 'access':
                    url = node_data.get('data', {}).get('url', '')
                    login = node_data.get('data', {}).get('login', '')
                    password = node_data.get('data', {}).get('password', '')

                    if not db_id and login:
                        acc = Access.objects.create(
                            project=project,
                            url=url,
                            login=login,
                            password=password
                        )
                        node_data['data']['db_id'] = acc.id
                        node_data['id'] = f"access_{acc.id}"

                elif node_type == 'billing':
                    amount = node_data.get('data', {}).get('amount')
                    operation = node_data.get('status', 'expense')

                    if not db_id and amount:
                        bill = Billing.objects.create(
                            project=project,
                            amount=amount,
                            operation=operation,
                            date=timezone.now().date(),
                            tag='planned_expense'
                        )
                        node_data['data']['db_id'] = bill.id
                        node_data['id'] = f"billing_{bill.id}"

            project.structure_data = data
            project.save()
            return Response(data)
