from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from apps.projects.models import Project, ProjectMembership
from apps.users.models import GroupUsers
from apps.access.models import Access
from apps.tasks.models import Task, SubTask
from .models import Billing


class ProjectRecordWorkflowTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.admin = users.objects.create_user(username='admin', email='admin@example.test', is_superuser=True)
        self.owner = users.objects.create_user(username='owner', email='owner@example.test')
        self.member = users.objects.create_user(username='member', email='member@example.test')
        self.project = Project.objects.create(name='Owned project', u_creator=self.owner)
        self.other = Project.objects.create(name='Other project', u_creator=self.admin)
        ProjectMembership.objects.create(project=self.project, user=self.member, role='member')
        self.billing = Billing.objects.create(project=self.project, amount='100.00', date='2026-10-29', operation='income', tag='actual_income')
        self.access = Access.objects.create(project=self.project, login='demo', password='fake-password')
        self.client.force_login(self.admin)

    def payload(self, app, project):
        if app == 'billing':
            return dict(project=project.pk, amount='250.50', date='2026-10-29', operation='income', tag='actual_income', description='Demo')
        return dict(project=project.pk, login='updated-demo', password='fake-secret', url='https://example.com', tags='[]')

    def test_admin_actions_and_visible_project_choice(self):
        for app in ['billing', 'access']:
            response = self.client.get(reverse(f'{app}:{app}_list'))
            self.assertContains(response, reverse(f'{app}:{app}_create'))
            obj = getattr(self, app)
            for action in ['edit', 'delete']:
                self.assertContains(response, reverse(f'{app}:{app}_{action}', kwargs={'pk':obj.pk}))
            response = self.client.get(reverse(f'{app}:{app}_create'), {'project':self.project.pk})
            self.assertContains(response, 'id="id_project"')
            self.assertContains(response, f'value="{self.project.pk}" selected')
            self.assertNotContains(response, '<div class="d-none"><select')

    def test_create_edit_delete_for_selected_project(self):
        for app, model in [('billing', Billing), ('access', Access)]:
            response = self.client.post(reverse(f'{app}:{app}_create'), self.payload(app,self.other))
            self.assertEqual(response.status_code, 302)
            obj = model.objects.latest('pk')
            self.assertEqual(obj.project, self.other)
            response = self.client.post(reverse(f'{app}:{app}_edit',kwargs={'pk':obj.pk}), self.payload(app,self.project))
            self.assertEqual(response.status_code,302)
            self.assertEqual(self.client.get(response.url).status_code,200)
            obj.refresh_from_db(); self.assertEqual(obj.project,self.project)
            path = reverse(f'{app}:{app}_delete',kwargs={'pk':obj.pk})
            self.assertContains(self.client.get(path), self.project.name)
            self.assertTrue(model.objects.filter(pk=obj.pk).exists())
            self.assertEqual(self.client.post(path).status_code,302)
            self.assertFalse(model.objects.filter(pk=obj.pk).exists())

    def test_invalid_forms_keep_project_choice_and_errors(self):
        for app in ['billing','access']:
            response = self.client.post(reverse(f'{app}:{app}_create'), {'project':self.project.pk})
            self.assertEqual(response.status_code,200)
            self.assertContains(response,'role="alert"')
            self.assertContains(response,'id="id_project"')

    def test_member_cannot_write_and_owner_cannot_use_foreign_project(self):
        self.client.force_login(self.member)
        for app in ['billing','access']:
            obj = getattr(self,app)
            for action in ['edit','delete']:
                path = reverse(f'{app}:{app}_{action}',kwargs={'pk':obj.pk})
                self.assertEqual(self.client.get(path).status_code,404)
                self.assertEqual(self.client.post(path,self.payload(app,self.project)).status_code,404)
            response = self.client.get(reverse(f'{app}:{app}_list'))
            self.assertNotContains(response,reverse(f'{app}:{app}_create'))
        self.client.force_login(self.owner)
        for app in ['billing','access']:
            response = self.client.post(reverse(f'{app}:{app}_create'),self.payload(app,self.other))
            self.assertEqual(response.status_code,200)
            self.assertNotContains(response, f'<option value="{self.other.pk}">{self.other.name}</option>')
            self.assertEqual(self.client.post(reverse(f'{app}:{app}_create'),self.payload(app,self.project)).status_code,302)

    def test_group_admin_has_record_management(self):
        self.member.u_group = GroupUsers.objects.create(name='admin')
        self.member.save(update_fields=['u_group'])
        self.client.force_login(self.member)
        for app in ['billing','access']:
            self.assertContains(self.client.get(reverse(f'{app}:{app}_list')),reverse(f'{app}:{app}_create'))
            self.assertEqual(self.client.post(reverse(f'{app}:{app}_create'),self.payload(app,self.other)).status_code,302)

    def test_task_delete_confirmation_and_project_scope(self):
        task = Task.objects.create(project=self.project,title='Delete demo task')
        subtask = SubTask.objects.create(task=task,title='Demo subtask')
        path = reverse('tasks:task_delete',kwargs={'pk':task.pk})
        self.assertContains(self.client.get(reverse('tasks:task_list')),path)
        self.assertContains(self.client.get(reverse('tasks:task_detail',kwargs={'pk':task.pk})),path)
        self.assertContains(self.client.get(path),self.project.name)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
        self.client.force_login(self.member)
        foreign = Task.objects.create(project=self.other,title='Private task')
        self.assertEqual(self.client.post(reverse('tasks:task_delete',kwargs={'pk':foreign.pk})).status_code,404)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(path).status_code,302)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
        self.assertFalse(SubTask.objects.filter(pk=subtask.pk).exists())

    def test_pagination_and_password_mask(self):
        Billing.objects.bulk_create([Billing(project=self.project,amount=1,date='2026-10-29',operation='income',tag='actual_income') for _ in range(21)])
        self.assertContains(self.client.get(reverse('billing:billing_list')),'?page=2')
        response = self.client.get(reverse('access:access_edit',kwargs={'pk':self.access.pk}))
        self.assertContains(response,'type="password"')

    def test_expanded_project_task_table(self):
        task = Task.objects.create(project=self.project,title='Table demo',estimated_time=16,actual_time=8)
        SubTask.objects.create(task=task,title='Done',status='done')
        SubTask.objects.create(task=task,title='Pending')
        self.client.force_login(self.owner)
        response = self.client.get(reverse('projects:project_detail',kwargs={'pk':self.project.pk}))
        self.assertContains(response, 'aria-valuenow="50"')
        self.assertContains(response, 'data-label="Підзадачі"')
        self.assertContains(response, '1 люд.-дн.')
        for action in ['edit','delete']:
            self.assertContains(response, reverse(f'tasks:task_{action}',kwargs={'pk':task.pk}))
