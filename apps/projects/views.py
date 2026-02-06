import json
from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .forms import ProjectForm
from .models import Tag, Project, ProjectMembership
from .serializers import *
from apps.tasks.models import Task, SubTask
from apps.access.models import Access
from apps.billing.models import Billing
from apps.media_files.models import MediaFile

User = get_user_model()


class OwnerAdminMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        if isinstance(obj, Project):
            project = obj
        else:
            project = obj.project
        return self.request.user.is_superuser or \
            ProjectMembership.objects.filter(project=project, user=self.request.user, role='owner').exists()


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(
            Q(u_creator=self.request.user) | Q(members__user=self.request.user)
        ).distinct()

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

    def get_queryset(self):
        return Project.objects.filter(
            Q(u_creator=self.request.user) | Q(members__user=self.request.user)
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        project = self.object

        membership = ProjectMembership.objects.filter(project=project, user=user).first()
        context['current_membership'] = membership
        context['is_owner'] = user.is_superuser or (membership and membership.role == 'owner')
        return context


class ProjectStructureView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/structure.html'
    context_object_name = 'project'

    def get_queryset(self):
        return Project.objects.filter(
            Q(u_creator=self.request.user) | Q(members__user=self.request.user)
        ).distinct()


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


class ProjectUpdateView(LoginRequiredMixin, OwnerAdminMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})


class ProjectDeleteView(LoginRequiredMixin, OwnerAdminMixin, DeleteView):
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

        is_owner = request.user.is_superuser or \
                   project.u_creator == request.user or \
                   ProjectMembership.objects.filter(project=project, user=request.user, role='owner').exists()

        if not is_owner and request.method == 'POST':
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            structure = project.structure_data or {'nodes': [], 'connections': []}
            if isinstance(structure, str):
                structure = json.loads(structure)

            nodes = structure.get('nodes', [])
            connections = structure.get('connections', [])

            project_users = User.objects.filter(
                Q(project_memberships__project=project) |
                Q(id=project.u_creator.id)
            ).distinct()

            users_data = [{'id': u.id, 'username': u.username} for u in project_users]

            db_tasks_map = {t.id: t for t in Task.objects.filter(project=project)}
            db_subtasks_map = {st.id: st for st in SubTask.objects.filter(task__project=project)}
            db_access_map = {a.id: a for a in Access.objects.filter(project=project)}
            db_billing_map = {b.id: b for b in Billing.objects.filter(project=project)}
            db_media_map = {m.id: m for m in MediaFile.objects.filter(project=project)}

            cleaned_nodes = []

            for node in nodes:
                n_type = node.get('type')
                db_id = node.get('data', {}).get('db_id')

                if n_type == 'project':
                    cleaned_nodes.append(node)
                    continue

                if not db_id:
                    cleaned_nodes.append(node)
                    continue

                if n_type == 'task':
                    if db_id in db_tasks_map:
                        task = db_tasks_map[db_id]
                        node['title'] = task.title
                        node['status'] = task.status
                        node['data']['title'] = task.title
                        node['data']['assignee'] = task.u_users.first().id if task.u_users.exists() else ""
                        cleaned_nodes.append(node)
                elif n_type == 'subtask':
                    if db_id in db_subtasks_map:
                        sub = db_subtasks_map[db_id]
                        node['title'] = sub.title
                        node['status'] = sub.status
                        node['data']['title'] = sub.title
                        node['data']['assignee'] = sub.u_users.first().id if sub.u_users.exists() else ""
                        cleaned_nodes.append(node)
                elif n_type == 'access':
                    if db_id in db_access_map:
                        acc = db_access_map[db_id]
                        node['title'] = acc.description or acc.login or "Access"
                        node['data']['login'] = acc.login
                        node['data']['url'] = acc.url
                        node['data']['password'] = acc.password
                        cleaned_nodes.append(node)
                elif n_type == 'billing':
                    if db_id in db_billing_map:
                        bill = db_billing_map[db_id]
                        node['title'] = f"{bill.amount} ({bill.get_operation_display()})"
                        node['status'] = bill.operation
                        node['data']['amount'] = str(bill.amount)
                        cleaned_nodes.append(node)
                elif n_type == 'media':
                    if db_id in db_media_map:
                        media = db_media_map[db_id]
                        title = media.description or media.filename
                        node['title'] = title
                        node['data']['title'] = title
                        cleaned_nodes.append(node)

            valid_node_ids = {n['id'] for n in cleaned_nodes}

            cleaned_connections = []
            for c in connections:
                source = c.get('source')
                target = c.get('target')
                if source in valid_node_ids and target in valid_node_ids:
                    cleaned_connections.append(c)

            nodes = cleaned_nodes
            connections = cleaned_connections

            existing_ids = {
                (n.get('type'), n.get('data', {}).get('db_id')): n
                for n in nodes
                if n.get('data', {}).get('db_id')
            }

            existing_conn_keys = set()
            for c in connections:
                existing_conn_keys.add(f"{c['source']}->{c['target']}")

            for task in db_tasks_map.values():
                if ('task', task.id) not in existing_ids:
                    nodes.append({
                        "id": f"task_{task.id}",
                        "type": "task",
                        "title": task.title,
                        "status": task.status,
                        "x": 100,
                        "y": 100 + len(nodes) * 50,
                        "data": {
                            "db_id": task.id,
                            "title": task.title,
                            "assignee": task.u_users.first().id if task.u_users.exists() else ""
                        }
                    })

            for sub in db_subtasks_map.values():
                sub_node_id = f"subtask_{sub.id}"
                task_node_id = f"task_{sub.task.id}" if sub.task else None

                if ('subtask', sub.id) not in existing_ids:
                    nodes.append({
                        "id": sub_node_id,
                        "type": "subtask",
                        "title": sub.title,
                        "status": sub.status,
                        "x": 300,
                        "y": 100 + len(nodes) * 50,
                        "data": {
                            "db_id": sub.id,
                            "title": sub.title,
                            "assignee": sub.u_users.first().id if sub.u_users.exists() else ""
                        }
                    })

                if task_node_id:
                    conn_key = f"{task_node_id}->{sub_node_id}"
                    if conn_key not in existing_conn_keys:
                        connections.append({
                            "source": task_node_id,
                            "target": sub_node_id
                        })
                        existing_conn_keys.add(conn_key)

            for acc in db_access_map.values():
                if ('access', acc.id) not in existing_ids:
                    nodes.append({
                        "id": f"access_{acc.id}",
                        "type": "access",
                        "title": acc.description or acc.login or "Access",
                        "status": "active",
                        "x": 400,
                        "y": 100 + len(nodes) * 50,
                        "data": {"db_id": acc.id, "login": acc.login, "url": acc.url, "password": acc.password}
                    })

            for bill in db_billing_map.values():
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

            for media in db_media_map.values():
                if ('media', media.id) not in existing_ids:
                    nodes.append({
                        "id": f"media_{media.id}",
                        "type": "media",
                        "title": media.description or media.filename,
                        "status": "active",
                        "x": 1000,
                        "y": 100 + len(nodes) * 50,
                        "data": {"db_id": media.id, "title": media.description or media.filename}
                    })

            return Response({"nodes": nodes, "connections": connections, "users": users_data})

        elif request.method == 'POST':
            data = request.data
            nodes = data.get('nodes', [])
            connections = data.get('connections', [])

            task_ids = []
            subtask_ids = []
            access_ids = []
            billing_ids = []
            media_ids = []

            node_id_to_db_id_map = {}
            original_to_new_id_map = {}

            for node_data in nodes:
                node_type = node_data.get('type')
                db_id = node_data.get('data', {}).get('db_id')

                if db_id:
                    node_id_to_db_id_map[node_data['id']] = {'type': node_type, 'db_id': db_id}
                    original_to_new_id_map[node_data['id']] = node_data['id']

                if not db_id: continue

                if node_type == 'task':
                    task_ids.append(db_id)
                elif node_type == 'subtask':
                    subtask_ids.append(db_id)
                elif node_type == 'access':
                    access_ids.append(db_id)
                elif node_type == 'billing':
                    billing_ids.append(db_id)
                elif node_type == 'media':
                    media_ids.append(db_id)

            Task.objects.filter(project=project).exclude(id__in=task_ids).delete()
            SubTask.objects.filter(task__project=project).exclude(id__in=subtask_ids).delete()
            Access.objects.filter(project=project).exclude(id__in=access_ids).delete()
            Billing.objects.filter(project=project).exclude(id__in=billing_ids).delete()
            MediaFile.objects.filter(project=project).exclude(id__in=media_ids).delete()

            SubTask.objects.filter(task__project=project).update(task=None)

            for node_data in nodes:
                node_type = node_data.get('type')
                db_id = node_data.get('data', {}).get('db_id')
                original_id = node_data['id']

                if node_type == 'task':
                    title = node_data.get('data', {}).get('title', 'New Task')
                    status_val = node_data.get('status', 'todo')
                    assignee_id = node_data.get('data', {}).get('assignee')

                    if db_id:
                        task = Task.objects.get(pk=db_id, project=project)
                        task.title = title
                        task.status = status_val
                        task.save()
                    else:
                        task = Task.objects.create(project=project, title=title, status=status_val)
                        node_data['data']['db_id'] = task.id
                        node_data['id'] = f"task_{task.id}"
                        node_id_to_db_id_map[original_id] = {'type': 'task', 'db_id': task.id}
                        original_to_new_id_map[original_id] = node_data['id']

                    task.u_users.clear()
                    if assignee_id:
                        task.u_users.add(assignee_id)

                elif node_type == 'subtask':
                    title = node_data.get('data', {}).get('title', 'New Subtask')
                    status_val = node_data.get('status', 'todo')
                    assignee_id = node_data.get('data', {}).get('assignee')

                    if db_id:
                        sub = SubTask.objects.get(pk=db_id)
                        sub.title = title
                        sub.status = status_val
                        sub.save()
                        node_id_to_db_id_map[original_id] = {'type': 'subtask', 'db_id': sub.id}
                        original_to_new_id_map[original_id] = original_id
                    else:
                        sub = SubTask.objects.create(title=title, status=status_val, task=None)
                        node_data['data']['db_id'] = sub.id
                        node_data['id'] = f"subtask_{sub.id}"
                        node_id_to_db_id_map[original_id] = {'type': 'subtask', 'db_id': sub.id}
                        original_to_new_id_map[original_id] = node_data['id']

                    sub.u_users.clear()
                    if assignee_id:
                        sub.u_users.add(assignee_id)

                elif node_type == 'access':
                    url = node_data.get('data', {}).get('url', '')
                    login = node_data.get('data', {}).get('login', '')
                    password = node_data.get('data', {}).get('password', '')
                    if db_id:
                        Access.objects.filter(pk=db_id, project=project).update(url=url, login=login, password=password)
                        node_id_to_db_id_map[original_id] = {'type': 'access', 'db_id': db_id}
                        original_to_new_id_map[original_id] = original_id
                    elif login:
                        acc = Access.objects.create(project=project, url=url, login=login, password=password)
                        node_data['data']['db_id'] = acc.id
                        node_data['id'] = f"access_{acc.id}"
                        node_id_to_db_id_map[original_id] = {'type': 'access', 'db_id': acc.id}
                        original_to_new_id_map[original_id] = node_data['id']

                elif node_type == 'billing':
                    amount = node_data.get('data', {}).get('amount')
                    operation = node_data.get('status', 'expense')
                    if db_id:
                        Billing.objects.filter(pk=db_id, project=project).update(amount=amount, operation=operation)
                        node_id_to_db_id_map[original_id] = {'type': 'billing', 'db_id': db_id}
                        original_to_new_id_map[original_id] = original_id
                    elif amount:
                        bill = Billing.objects.create(project=project, amount=amount, operation=operation,
                                                      date=timezone.now().date(), tag='planned')
                        node_data['data']['db_id'] = bill.id
                        node_data['id'] = f"billing_{bill.id}"
                        node_id_to_db_id_map[original_id] = {'type': 'billing', 'db_id': bill.id}
                        original_to_new_id_map[original_id] = node_data['id']

                elif node_type == 'media':
                    title = node_data.get('data', {}).get('title', '')
                    if db_id:
                        MediaFile.objects.filter(pk=db_id, project=project).update(description=title)
                        node_id_to_db_id_map[original_id] = {'type': 'media', 'db_id': db_id}
                        original_to_new_id_map[original_id] = original_id

            new_connections = []
            for conn in connections:
                source_id = conn.get('source')
                target_id = conn.get('target')

                source_info = node_id_to_db_id_map.get(source_id)
                target_info = node_id_to_db_id_map.get(target_id)

                new_source = original_to_new_id_map.get(source_id, source_id)
                new_target = original_to_new_id_map.get(target_id, target_id)
                conn['source'] = new_source
                conn['target'] = new_target
                new_connections.append(conn)

                if source_info and target_info:
                    if source_info['type'] == 'task' and target_info['type'] == 'subtask':
                        task_db_id = source_info['db_id']
                        subtask_db_id = target_info['db_id']
                        SubTask.objects.filter(pk=subtask_db_id).update(task_id=task_db_id)

            data['nodes'] = nodes
            data['connections'] = new_connections

            project.structure_data = json.dumps(data)
            project.save()
            return Response(data)
