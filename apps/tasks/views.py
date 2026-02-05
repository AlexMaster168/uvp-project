from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from .forms import TaskForm
from .models import Task
from .serializers import TaskSerializer, TaskCreateUpdateSerializer


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        project_id = self.request.GET.get('project')
        if project_id: qs = qs.filter(project_id=project_id)
        return qs


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_initial(self):
        return {'project': self.request.GET.get('project')}

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'project']
    search_fields = ['title']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']: return TaskCreateUpdateSerializer
        return TaskSerializer
