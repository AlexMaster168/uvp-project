from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from .forms import TaskForm, SubTaskForm
from .models import Task, SubTask
from .access import task_projects
from .serializers import TaskSerializer, TaskCreateUpdateSerializer, SubTaskSerializer


class TaskQuerysetMixin:
    def get_queryset(self):
        return Task.objects.filter(project__in=task_projects(self.request.user)).select_related('project').prefetch_related('u_users', 'subtasks')


class TaskListView(LoginRequiredMixin, TaskQuerysetMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        project_id = self.request.GET.get('project')
        if project_id:
            if not project_id.isdecimal(): return qs.none()
            qs = qs.filter(project_id=project_id)
        query = self.request.GET.get('q', '').strip()
        if query: qs = qs.filter(title__icontains=query)
        status = self.request.GET.get('status')
        if status in dict(Task.STATUS_CHOICES): qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_projects'] = task_projects(self.request.user)
        context['task_statuses'] = Task.STATUS_CHOICES
        context['editable_project_ids'] = set(task_projects(self.request.user).filter(
            Q(u_creator=self.request.user) | Q(members__user=self.request.user, members__role='owner')
        ).values_list('pk', flat=True))
        params = self.request.GET.copy()
        params.pop('page', None)
        context['task_filter_query'] = params.urlencode()
        return context


class TaskDetailView(LoginRequiredMixin, TaskQuerysetMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_manage_task'] = True
        from apps.projects.reporting import management_report
        context['task_report'] = management_report(self.object.project, [self.object])['rows'][0]
        context['can_manage_project'] = self.request.user.is_superuser or self.object.project.u_creator_id == self.request.user.pk or self.object.project.members.filter(user=self.request.user, role='owner').exists()
        return context


class TaskFormUserMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        SubTask.objects.bulk_create([SubTask(task=self.object, title=title) for title in form.cleaned_data.get('initial_subtasks', [])])
        return response


class TaskCreateView(LoginRequiredMixin, TaskFormUserMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_initial(self):
        return {'project': self.request.GET.get('project')}

    def get_success_url(self):
        return reverse_lazy('tasks:task_detail', kwargs={'pk': self.object.pk})


class TaskUpdateView(LoginRequiredMixin, TaskQuerysetMixin, TaskFormUserMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_success_url(self):
        return reverse_lazy('tasks:task_detail', kwargs={'pk': self.object.pk})


class TaskDeleteView(LoginRequiredMixin, TaskQuerysetMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('tasks:task_list') + '?project=' + str(self.object.project_id)


class TaskProjectMembersView(LoginRequiredMixin, View):
    def get(self, request):
        project_id = request.GET.get('project', '')
        if not project_id.isdecimal(): raise Http404
        project = task_projects(request.user).filter(pk=project_id).first()
        if project is None: raise Http404
        users = get_user_model().objects.filter(Q(project_memberships__project=project) | Q(pk=project.u_creator_id)).distinct()
        return JsonResponse({'users': [{'id': user.pk, 'name': user.username} for user in users]})


class SubTaskQuerysetMixin:
    def get_queryset(self):
        return SubTask.objects.filter(task__project__in=task_projects(self.request.user)).select_related('task__project').prefetch_related('u_users')


class SubTaskDetailView(LoginRequiredMixin, SubTaskQuerysetMixin, DetailView):
    model = SubTask
    context_object_name = 'subtask'
    template_name = 'tasks/subtask_detail.html'


class SubTaskFormUserMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy('tasks:subtask_detail', kwargs={'pk': self.object.pk})


class SubTaskCreateView(LoginRequiredMixin, SubTaskFormUserMixin, CreateView):
    model = SubTask
    form_class = SubTaskForm
    template_name = 'tasks/subtask_form.html'

    def get_initial(self):
        return {'task': self.request.GET.get('task')}


class SubTaskUpdateView(LoginRequiredMixin, SubTaskQuerysetMixin, SubTaskFormUserMixin, UpdateView):
    model = SubTask
    form_class = SubTaskForm
    template_name = 'tasks/subtask_form.html'


class SubTaskDeleteView(LoginRequiredMixin, SubTaskQuerysetMixin, DeleteView):
    model = SubTask
    template_name = 'tasks/subtask_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('tasks:task_detail', kwargs={'pk': self.object.task_id})


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'project']
    search_fields = ['title']

    def get_queryset(self):
        return Task.objects.filter(project__in=task_projects(self.request.user)).select_related('project').prefetch_related('u_users','subtasks')

    def _save(self, serializer):
        project = serializer.validated_data.get('project') or getattr(serializer.instance, 'project', None)
        if project is None or not task_projects(self.request.user).filter(pk=project.pk).exists():
            raise PermissionDenied('Недоступний проєкт.')
        validate_assignees(serializer, project)
        serializer.save()

    def perform_create(self, serializer):
        self._save(serializer)

    def perform_update(self, serializer):
        self._save(serializer)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']: return TaskCreateUpdateSerializer
        return TaskSerializer


class SubTaskViewSet(viewsets.ModelViewSet):
    queryset = SubTask.objects.all()
    serializer_class = SubTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['task']

    def get_queryset(self):
        return SubTask.objects.filter(task__project__in=task_projects(self.request.user))

    def _save(self, serializer):
        task = serializer.validated_data.get('task', getattr(serializer.instance, 'task', None))
        if task is None or not task_projects(self.request.user).filter(pk=task.project_id).exists():
            raise PermissionDenied('Недоступна батьківська задача.')
        validate_assignees(serializer, task.project)
        serializer.save()

    def perform_create(self, serializer):
        self._save(serializer)

    def perform_update(self, serializer):
        self._save(serializer)


def validate_assignees(serializer, project):
    users = serializer.validated_data.get('u_users')
    if users is None:
        return
    allowed = set(get_user_model().objects.filter(Q(project_memberships__project=project) | Q(pk=project.u_creator_id)).values_list('pk', flat=True))
    if any(user.pk not in allowed for user in users):
        raise ValidationError({'u_users':'Виконавці мають належати до обраного проєкту.'})
