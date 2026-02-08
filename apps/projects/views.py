import json
from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters, status, views
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


class SuperStructureView(LoginRequiredMixin, TemplateView):
    template_name = 'projects/super_structure.html'


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

    @action(detail=False, methods=['get', 'post'], url_path='super-structure')
    def super_structure(self, request):
        if request.method == 'GET':
            user = request.user
            projects = Project.objects.filter(
                Q(u_creator=user) | Q(members__user=user)
            ).distinct()

            nodes = []
            connections = []
            current_y = 50

            for project in projects:
                project_node_id = f"project_{project.id}"
                nodes.append({
                    "id": project_node_id,
                    "type": "project",
                    "title": project.name,
                    "status": project.status,
                    "x": 50,
                    "y": current_y,
                    "data": {"db_id": project.id, "title": project.name}
                })

                tasks = Task.objects.filter(project=project)
                task_x = 350
                task_y = current_y

                for task in tasks:
                    task_node_id = f"task_{task.id}"
                    nodes.append({
                        "id": task_node_id,
                        "type": "task",
                        "title": task.title,
                        "status": task.status,
                        "x": task_x,
                        "y": task_y,
                        "data": {
                            "db_id": task.id,
                            "title": task.title,
                            "project_id": project.id,
                            "assignee": task.u_users.first().id if task.u_users.exists() else ""
                        }
                    })
                    connections.append({"source": project_node_id, "target": task_node_id})

                    for next_task in task.next_tasks.all():
                        connections.append({"source": task_node_id, "target": f"task_{next_task.id}"})

                    subtasks = SubTask.objects.filter(task=task)
                    sub_y = task_y
                    for sub in subtasks:
                        sub_node_id = f"subtask_{sub.id}"
                        nodes.append({
                            "id": sub_node_id,
                            "type": "subtask",
                            "title": sub.title,
                            "status": sub.status,
                            "x": task_x + 300,
                            "y": sub_y,
                            "data": {
                                "db_id": sub.id,
                                "title": sub.title,
                                "project_id": project.id,
                                "assignee": sub.u_users.first().id if sub.u_users.exists() else ""
                            }
                        })
                        connections.append({"source": task_node_id, "target": sub_node_id})
                        sub_y += 100

                    task_y = max(task_y + 120, sub_y + 50)

                accesses = Access.objects.filter(project=project)
                acc_y = current_y + (len(tasks) * 50)
                for acc in accesses:
                    acc_node_id = f"access_{acc.id}"
                    nodes.append({
                        "id": acc_node_id,
                        "type": "access",
                        "title": acc.description or acc.login,
                        "status": "active",
                        "x": 350,
                        "y": acc_y,
                        "data": {"db_id": acc.id, "login": acc.login, "url": acc.url, "password": acc.password,
                                 "project_id": project.id}
                    })
                    connections.append({"source": project_node_id, "target": acc_node_id})
                    acc_y += 100

                billings = Billing.objects.filter(project=project)
                bill_y = acc_y
                for bill in billings:
                    bill_node_id = f"billing_{bill.id}"
                    nodes.append({
                        "id": bill_node_id,
                        "type": "billing",
                        "title": f"{bill.amount}",
                        "status": bill.operation,
                        "x": 350,
                        "y": bill_y,
                        "data": {"db_id": bill.id, "amount": str(bill.amount), "project_id": project.id}
                    })
                    connections.append({"source": project_node_id, "target": bill_node_id})
                    bill_y += 100

                medias = MediaFile.objects.filter(project=project)
                media_y = bill_y
                for media in medias:
                    media_node_id = f"media_{media.id}"
                    nodes.append({
                        "id": media_node_id,
                        "type": "media",
                        "title": media.description or media.file.name,
                        "status": "active",
                        "x": 350,
                        "y": media_y,
                        "data": {"db_id": media.id, "title": media.description, "project_id": project.id}
                    })
                    connections.append({"source": project_node_id, "target": media_node_id})
                    media_y += 100

                current_y = max(task_y, media_y) + 200

            users_data = [{'id': u.id, 'username': u.username} for u in User.objects.all()]

            return Response({"nodes": nodes, "connections": connections, "users": users_data})

        elif request.method == 'POST':
            data = request.data
            nodes = data.get('nodes', [])
            connections = data.get('connections', [])
            user = request.user

            task_ids = []
            subtask_ids = []
            access_ids = []
            billing_ids = []
            media_ids = []

            node_map = {}

            for n in nodes:
                if n['type'] == 'project':
                    db_id = n.get('data', {}).get('db_id')
                    if db_id:
                        p = Project.objects.get(pk=db_id)
                        p.name = n.get('data', {}).get('title', p.name)
                        p.status = n.get('status', p.status)
                        p.save()
                        node_map[n['id']] = {'type': 'project', 'db_id': p.id, 'project_id': p.id}

            for n in nodes:
                if n['type'] == 'project': continue

                client_id = n['id']
                n_type = n['type']
                db_id = n.get('data', {}).get('db_id')

                project_id = n.get('data', {}).get('project_id')
                if not project_id:
                    for conn in connections:
                        if conn['target'] == client_id:
                            source_id = conn['source']
                            if source_id in node_map and node_map[source_id]['type'] == 'project':
                                project_id = node_map[source_id]['db_id']
                                break

                if n_type == 'task':
                    title = n.get('data', {}).get('title', 'New Task')
                    status_val = n.get('status', 'todo')
                    assignee = n.get('data', {}).get('assignee')

                    if db_id:
                        t = Task.objects.get(pk=db_id)
                        t.title = title
                        t.status = status_val
                        if assignee: t.u_users.set([assignee])
                        t.save()
                        node_map[client_id] = {'type': 'task', 'db_id': t.id, 'project_id': t.project_id}
                        task_ids.append(t.id)
                    elif project_id:
                        t = Task.objects.create(project_id=project_id, title=title, status=status_val)
                        if assignee: t.u_users.set([assignee])
                        node_map[client_id] = {'type': 'task', 'db_id': t.id, 'project_id': project_id}
                        task_ids.append(t.id)

                elif n_type == 'subtask':
                    title = n.get('data', {}).get('title', 'New Subtask')
                    status_val = n.get('status', 'todo')
                    assignee = n.get('data', {}).get('assignee')

                    if db_id:
                        st = SubTask.objects.get(pk=db_id)
                        st.title = title
                        st.status = status_val
                        if assignee: st.u_users.set([assignee])
                        st.save()
                        node_map[client_id] = {'type': 'subtask', 'db_id': st.id}
                        subtask_ids.append(st.id)
                    else:
                        st = SubTask.objects.create(title=title, status=status_val, task=None)
                        if assignee: st.u_users.set([assignee])
                        node_map[client_id] = {'type': 'subtask', 'db_id': st.id}
                        subtask_ids.append(st.id)

                elif n_type == 'access':
                    login = n.get('data', {}).get('login', 'login')
                    url = n.get('data', {}).get('url', '')
                    pwd = n.get('data', {}).get('password', '')
                    if db_id:
                        Access.objects.filter(pk=db_id).update(login=login, url=url, password=pwd)
                        node_map[client_id] = {'type': 'access', 'db_id': db_id}
                        access_ids.append(db_id)
                    elif project_id:
                        a = Access.objects.create(project_id=project_id, login=login, url=url, password=pwd)
                        node_map[client_id] = {'type': 'access', 'db_id': a.id}
                        access_ids.append(a.id)

                elif n_type == 'billing':
                    amount = n.get('data', {}).get('amount', 0)
                    op = n.get('status', 'expense')
                    if db_id:
                        Billing.objects.filter(pk=db_id).update(amount=amount, operation=op)
                        node_map[client_id] = {'type': 'billing', 'db_id': db_id}
                        billing_ids.append(db_id)
                    elif project_id:
                        b = Billing.objects.create(project_id=project_id, amount=amount, operation=op,
                                                   date=timezone.now().date(), tag='planned')
                        node_map[client_id] = {'type': 'billing', 'db_id': b.id}
                        billing_ids.append(b.id)

                elif n_type == 'media':
                    title = n.get('data', {}).get('title', '')
                    if db_id:
                        MediaFile.objects.filter(pk=db_id).update(description=title)
                        node_map[client_id] = {'type': 'media', 'db_id': db_id}
                        media_ids.append(db_id)

            user_projects = Project.objects.filter(Q(u_creator=user) | Q(members__user=user))

            Task.objects.filter(project__in=user_projects).exclude(id__in=task_ids).delete()
            SubTask.objects.filter(task__project__in=user_projects).exclude(id__in=subtask_ids).delete()
            Access.objects.filter(project__in=user_projects).exclude(id__in=access_ids).delete()
            Billing.objects.filter(project__in=user_projects).exclude(id__in=billing_ids).delete()
            MediaFile.objects.filter(project__in=user_projects).exclude(id__in=media_ids).delete()

            all_tasks = Task.objects.filter(project__in=user_projects)
            for t in all_tasks:
                t.previous_tasks.clear()

            for conn in connections:
                source = conn['source']
                target = conn['target']

                src_info = node_map.get(source)
                tgt_info = node_map.get(target)

                if src_info and tgt_info:
                    if src_info['type'] == 'task' and tgt_info['type'] == 'subtask':
                        SubTask.objects.filter(pk=tgt_info['db_id']).update(task_id=src_info['db_id'])

                    elif src_info['type'] == 'task' and tgt_info['type'] == 'task':
                        try:
                            t = Task.objects.get(pk=tgt_info['db_id'])
                            t.previous_tasks.add(src_info['db_id'])
                        except:
                            pass

                    elif src_info['type'] == 'project':
                        if tgt_info['type'] == 'task':
                            Task.objects.filter(pk=tgt_info['db_id']).update(project_id=src_info['db_id'])
                        elif tgt_info['type'] == 'access':
                            Access.objects.filter(pk=tgt_info['db_id']).update(project_id=src_info['db_id'])
                        elif tgt_info['type'] == 'billing':
                            Billing.objects.filter(pk=tgt_info['db_id']).update(project_id=src_info['db_id'])
                        elif tgt_info['type'] == 'media':
                            MediaFile.objects.filter(pk=tgt_info['db_id']).update(project_id=src_info['db_id'])

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
