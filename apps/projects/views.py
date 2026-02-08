import json
from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .forms import ProjectForm
from .models import Tag, Project, ProjectMembership
from .serializers import ProjectListSerializer, ProjectCreateUpdateSerializer, ProjectDetailSerializer, TagSerializer
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


class SuperStructureView(LoginRequiredMixin, TemplateView):
    template_name = 'projects/super_structure.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['superusers'] = User.objects.filter(is_superuser=True)
        return context


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['owners'] = User.objects.filter(project_memberships__role='owner').distinct()
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(
            Q(u_creator=self.request.user) | Q(members__user=self.request.user)
        ).distinct()

        q = self.request.GET.get('q')
        status_val = self.request.GET.get('status')
        owner_id = self.request.GET.get('owner')

        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(u_tags__name__icontains=q)
            ).distinct()

        if status_val:
            qs = qs.filter(status=status_val)

        if owner_id:
            qs = qs.filter(members__user_id=owner_id, members__role='owner')

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
        owner_id = self.request.data.get('owner_id')
        target_user = self.request.user

        if owner_id:
            try:
                target_user = User.objects.get(pk=owner_id)
            except User.DoesNotExist:
                pass

        project = serializer.save(u_creator=target_user)
        ProjectMembership.objects.create(project=project, user=target_user, role='owner')

    def perform_update(self, serializer):
        project = serializer.save()
        owner_id = self.request.data.get('owner_id')
        if owner_id:
            try:
                user = User.objects.get(pk=owner_id)
                project.u_creator = user
                project.save()
                ProjectMembership.objects.update_or_create(
                    project=project,
                    user=user,
                    defaults={'role': 'owner'}
                )
            except User.DoesNotExist:
                pass

    @action(detail=False, methods=['get', 'post'], url_path='super-structure')
    def super_structure(self, request):
        if request.method == 'GET':
            owners = User.objects.filter(is_superuser=True).distinct()
            nodes = []
            connections = []

            unsaved_y = 50

            for owner in owners:
                owner_id = f"owner_{owner.id}"

                if owner.global_x != 0 or owner.global_y != 0:
                    ox = owner.global_x
                    oy = owner.global_y
                else:
                    ox = 500
                    oy = unsaved_y
                    unsaved_y += 400

                nodes.append({
                    "id": owner_id,
                    "type": "owner",
                    "title": owner.username,
                    "status": "active",
                    "x": ox,
                    "y": oy,
                    "data": {"db_id": owner.id}
                })

                owner_projects = Project.objects.filter(members__user=owner, members__role='owner')
                unsaved_proj_offset = -300

                for proj in owner_projects:
                    proj_id = f"project_{proj.id}"

                    if not any(n['id'] == proj_id for n in nodes):
                        if proj.global_x != 0 or proj.global_y != 0:
                            px = proj.global_x
                            py = proj.global_y
                        else:
                            px = ox + unsaved_proj_offset
                            py = oy + 200
                            unsaved_proj_offset += 280

                        nodes.append({
                            "id": proj_id,
                            "type": "project",
                            "title": proj.name,
                            "status": proj.status,
                            "x": px,
                            "y": py,
                            "data": {
                                "db_id": proj.id,
                                "description": proj.description,
                                "status": proj.status,
                                "logo": proj.logo.url if proj.logo else '',
                                "owner_id": proj.u_creator.id
                            }
                        })

                    connections.append({
                        "source": owner_id,
                        "target": proj_id
                    })

            return Response({"nodes": nodes, "connections": connections})

        elif request.method == 'POST':
            data = request.data
            nodes = data.get('nodes', [])

            for n in nodes:
                db_id = n.get('data', {}).get('db_id')
                if not db_id:
                    continue

                if n['type'] == 'project':
                    Project.objects.filter(pk=db_id).update(
                        global_x=n.get('x', 0),
                        global_y=n.get('y', 0)
                    )
                elif n['type'] == 'owner':
                    User.objects.filter(pk=db_id).update(
                        global_x=n.get('x', 0),
                        global_y=n.get('y', 0)
                    )

            return Response({"status": "ok"})

    @action(detail=True, methods=['get', 'post'])
    def structure(self, request, pk=None):
        project = self.get_object()

        is_owner = request.user.is_superuser or \
                   project.u_creator == request.user or \
                   ProjectMembership.objects.filter(project=project, user=request.user, role='owner').exists()

        if not is_owner and request.method == 'POST':
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            saved_structure = {}
            if project.structure_data and isinstance(project.structure_data, str):
                saved_structure = json.loads(project.structure_data)

            saved_nodes = saved_structure.get('nodes', [])

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

            nodes = []
            connections = []

            saved_nodes_map = {
                (n.get('type'), n.get('data', {}).get('db_id')): n
                for n in saved_nodes
                if n.get('data', {}).get('db_id')
            }

            y_offset = 50

            for task in db_tasks_map.values():
                task_node_id = f"task_{task.id}"

                saved_node = saved_nodes_map.get(('task', task.id))
                x = saved_node['x'] if saved_node else 100
                y = saved_node['y'] if saved_node else y_offset
                if not saved_node: y_offset += 150

                nodes.append({
                    "id": task_node_id,
                    "type": "task",
                    "title": task.title,
                    "status": task.status,
                    "x": x,
                    "y": y,
                    "data": {
                        "db_id": task.id,
                        "title": task.title,
                        "assignee": task.u_users.first().id if task.u_users.exists() else ""
                    }
                })

                for next_task in task.next_tasks.all():
                    connections.append({
                        "source": task_node_id,
                        "target": f"task_{next_task.id}"
                    })

            for sub in db_subtasks_map.values():
                sub_node_id = f"subtask_{sub.id}"

                saved_node = saved_nodes_map.get(('subtask', sub.id))
                x = saved_node['x'] if saved_node else 400
                y = saved_node['y'] if saved_node else y_offset
                if not saved_node: y_offset += 150

                nodes.append({
                    "id": sub_node_id,
                    "type": "subtask",
                    "title": sub.title,
                    "status": sub.status,
                    "x": x,
                    "y": y,
                    "data": {
                        "db_id": sub.id,
                        "title": sub.title,
                        "assignee": sub.u_users.first().id if sub.u_users.exists() else ""
                    }
                })

                if sub.task:
                    connections.append({
                        "source": f"task_{sub.task.id}",
                        "target": sub_node_id
                    })

            for acc in db_access_map.values():
                node_id = f"access_{acc.id}"
                saved_node = saved_nodes_map.get(('access', acc.id))

                nodes.append({
                    "id": node_id,
                    "type": "access",
                    "title": acc.description or acc.login or "Access",
                    "status": "active",
                    "x": saved_node['x'] if saved_node else 600,
                    "y": saved_node['y'] if saved_node else y_offset,
                    "data": {"db_id": acc.id, "login": acc.login, "url": acc.url, "password": acc.password}
                })

            for bill in db_billing_map.values():
                node_id = f"billing_{bill.id}"
                saved_node = saved_nodes_map.get(('billing', bill.id))

                nodes.append({
                    "id": node_id,
                    "type": "billing",
                    "title": f"{bill.amount} ({bill.get_operation_display()})",
                    "status": bill.operation,
                    "x": saved_node['x'] if saved_node else 800,
                    "y": saved_node['y'] if saved_node else y_offset,
                    "data": {"db_id": bill.id, "amount": str(bill.amount)}
                })

            for media in db_media_map.values():
                node_id = f"media_{media.id}"
                saved_node = saved_nodes_map.get(('media', media.id))

                nodes.append({
                    "id": node_id,
                    "type": "media",
                    "title": media.description or media.filename,
                    "status": "active",
                    "x": saved_node['x'] if saved_node else 1000,
                    "y": saved_node['y'] if saved_node else y_offset,
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

            all_tasks = Task.objects.filter(project=project)
            for t in all_tasks:
                t.previous_tasks.clear()

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

                new_source = original_to_new_id_map.get(source_id, source_id)
                new_target = original_to_new_id_map.get(target_id, target_id)
                conn['source'] = new_source
                conn['target'] = new_target
                new_connections.append(conn)

                source_info = node_id_to_db_id_map.get(source_id)
                target_info = node_id_to_db_id_map.get(target_id)

                if source_info and target_info:
                    if source_info['type'] == 'task' and target_info['type'] == 'subtask':
                        task_db_id = source_info['db_id']
                        subtask_db_id = target_info['db_id']
                        SubTask.objects.filter(pk=subtask_db_id).update(task_id=task_db_id)

                    elif source_info['type'] == 'task' and target_info['type'] == 'task':
                        prev_task_id = source_info['db_id']
                        next_task_id = target_info['db_id']
                        try:
                            next_task = Task.objects.get(pk=next_task_id)
                            next_task.previous_tasks.add(prev_task_id)
                        except Task.DoesNotExist:
                            pass

            data['nodes'] = nodes
            data['connections'] = new_connections

            project.structure_data = json.dumps(data)
            project.save()
            return Response(data)
