from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from apps.projects.models import Project, ProjectMembership
from apps.users.models import GroupUsers
from .models import Task, SubTask


class TaskWorkflowTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user(username='owner', email='owner@example.test')
        self.member = users.objects.create_user(username='member', email='member@example.test')
        self.customer = users.objects.create_user(username='customer', email='customer@example.test')
        self.outsider = users.objects.create_user(username='outsider', email='outsider@example.test')
        self.project = Project.objects.create(name='Team project', u_creator=self.owner)
        ProjectMembership.objects.create(project=self.project, user=self.member, role='member')
        ProjectMembership.objects.create(project=self.project, user=self.customer, role='customer')
        self.task = Task.objects.create(project=self.project, title='Visible task', description='First line\n<script>unsafe</script>')
        self.subtask = SubTask.objects.create(task=self.task, title='Visible subtask')
        self.other_project = Project.objects.create(name='Private project', u_creator=self.outsider)
        self.other_task = Task.objects.create(project=self.other_project, title='Private task')
        self.client.force_login(self.owner)

    def test_task_list_create_and_subtask_links(self):
        response = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('tasks:task_create'))
        self.assertContains(response, reverse('tasks:subtask_create'))
        self.assertContains(response, reverse('projects:project_edit', kwargs={'pk':self.project.pk}))
        self.assertNotContains(response, 'Private task')
        response = self.client.get(reverse('tasks:task_detail', kwargs={'pk':self.task.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('tasks:subtask_edit', kwargs={'pk':self.subtask.pk}))
        self.assertContains(response, '&lt;script&gt;unsafe&lt;/script&gt;')

    def test_create_task_with_project_days_and_subtasks(self):
        response = self.client.post(reverse('tasks:task_create'), {
            'title':'New task', 'description':'Details', 'status':'todo', 'project':self.project.pk,
            'time_unit':'days', 'estimated_time':'2', 'actual_time':'0.5',
            'u_users':[self.member.pk], 'initial_subtasks':'Step one\nStep two',
        })
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title='New task')
        self.assertEqual(task.project, self.project)
        self.assertEqual(task.estimated_time, 16)
        self.assertEqual(task.actual_time, 4)
        self.assertEqual(task.subtasks.count(), 2)
        self.assertIn(self.member, task.u_users.all())

    def test_project_dropdown_and_member_endpoint(self):
        response = self.client.get(reverse('tasks:task_create'))
        self.assertContains(response, 'id="id_project"')
        self.assertContains(response, 'Team project')
        self.assertNotContains(response, 'Private project')
        response = self.client.get(reverse('tasks:project_members'), {'project':self.project.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.member.pk, [user['id'] for user in response.json()['users']])
        self.assertEqual(self.client.get(reverse('tasks:project_members'), {'project':self.other_project.pk}).status_code, 404)
        response = self.client.get(reverse('tasks:task_create'), {'project':self.other_project.pk})
        self.assertNotContains(response, '<option value="%s">outsider</option>' % self.outsider.pk)

    def test_forged_task_project_and_assignee_rejected(self):
        data = {'title':'Forged','status':'todo','project':self.other_project.pk,'estimated_time':0,'actual_time':0}
        response = self.client.post(reverse('tasks:task_create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(title='Forged').exists())
        response = self.client.post(reverse('tasks:task_create'), {**data,'project':self.project.pk,'u_users':[self.outsider.pk]})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(title='Forged').exists())

    def test_member_can_edit_task_and_subtask(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse('tasks:task_edit', kwargs={'pk':self.task.pk})).status_code, 200)
        response = self.client.post(reverse('tasks:subtask_edit', kwargs={'pk':self.subtask.pk}), {
            'task':self.task.pk,'title':'Renamed','status':'done','u_users':[self.member.pk],
        })
        self.assertEqual(response.status_code, 302)
        self.subtask.refresh_from_db()
        self.assertEqual(self.subtask.title, 'Renamed')
        self.assertEqual(self.subtask.status, 'done')

    def test_subtask_create_detail_delete(self):
        response = self.client.post(reverse('tasks:subtask_create'), {'task':self.task.pk,'title':'Added','status':'todo'})
        self.assertEqual(response.status_code, 302)
        added = SubTask.objects.get(title='Added')
        self.assertEqual(self.client.get(reverse('tasks:subtask_detail',kwargs={'pk':added.pk})).status_code, 200)
        self.assertEqual(self.client.post(reverse('tasks:subtask_delete',kwargs={'pk':added.pk})).status_code, 302)
        self.assertFalse(SubTask.objects.filter(pk=added.pk).exists())

    def test_outsider_and_customer_cannot_manage_internal_tasks(self):
        for user in [self.outsider, self.customer]:
            self.client.force_login(user)
            for name, pk in [('task_detail',self.task.pk),('task_edit',self.task.pk),('subtask_detail',self.subtask.pk),('subtask_edit',self.subtask.pk)]:
                self.assertEqual(self.client.get(reverse('tasks:'+name,kwargs={'pk':pk})).status_code, 404)
            response = self.client.get(reverse('tasks:task_list'))
            self.assertNotContains(response, 'Visible task')

    def test_project_creation_with_initial_task_and_subtasks(self):
        response = self.client.post(reverse('projects:project_create'), {
            'name':'Project with steps','status':'planned','initial_task_title':'First task','initial_subtasks':'One\nTwo',
        })
        self.assertEqual(response.status_code, 302)
        project = Project.objects.get(name='Project with steps')
        self.assertEqual(project.u_creator, self.owner)
        self.assertEqual(project.tasks.get().subtasks.count(), 2)

    def test_initial_subtasks_require_parent_and_bound_lengths(self):
        response = self.client.post(reverse('projects:project_create'), {'name':'Invalid project','status':'planned','initial_subtasks':'No parent'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.filter(name='Invalid project').exists())
        response = self.client.post(reverse('tasks:task_create'), {'title':'Too long','status':'todo','project':self.project.pk,'estimated_time':0,'actual_time':0,'initial_subtasks':'a'*256})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(title='Too long').exists())

    def test_detailed_customization_only_for_admin_roles(self):
        paths = [reverse('tasks:task_list'),reverse('tasks:task_detail',kwargs={'pk':self.task.pk}),reverse('tasks:task_create'),reverse('projects:project_list'),reverse('projects:super_structure')]
        for path in paths:
            response = self.client.get(path)
            self.assertNotContains(response, 'id="pagePreferences"')
            self.assertNotContains(response, 'id="projectTheme"')
            self.assertNotContains(response, 'data-bs-target="#colorsModal"')
        group = GroupUsers.objects.create(name='admin')
        self.owner.u_group = group; self.owner.save(update_fields=['u_group'])
        for path in paths:
            self.assertContains(self.client.get(path), 'id="pagePreferences"')
        self.owner.u_group = None; self.owner.is_superuser = True; self.owner.save(update_fields=['u_group','is_superuser'])
        self.assertContains(self.client.get(reverse('projects:project_list')), 'id="projectTheme"')

    def test_progress_block_replaces_default_finance_focus(self):
        response = self.client.get(reverse('projects:project_list'), {'mode':'1'})
        self.assertContains(response, 'project-execution')
        self.assertContains(response, 'Прогрес робіт')
        self.assertContains(response, 'project-finance d-none')

    def test_admin_personalization_in_each_main_section(self):
        self.owner.is_superuser = True; self.owner.save(update_fields=['is_superuser'])
        names = ['projects:project_list','projects:project_create','projects:dashboard','projects:super_structure',
                 'tasks:task_list','tasks:task_create','billing:billing_list','access:access_list',
                 'media_files:media_list','users:user_list','users:profile','users:settings']
        for name in names:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            self.assertContains(response, 'id="pagePreferences"')
        response = self.client.get(reverse('projects:structure', kwargs={'pk':self.project.pk}))
        self.assertContains(response, 'id="pagePreferences"')

    def test_ordinary_modern_view_has_no_detailed_settings(self):
        response = self.client.get(reverse('projects:project_detail',kwargs={'pk':self.project.pk}), {'mode':'6'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="medusaTheme"')
        self.assertNotContains(response, 'id="pagePreferences"')
        self.assertContains(response, 'id="medusaLayout"')

    def test_ordinary_profile_role_badge(self):
        response = self.client.get(reverse('users:profile'))
        self.assertContains(response, 'bg-secondary rounded-pill px-3 py-2')
        self.assertNotContains(response, 'bg-primary rounded-pill px-3 py-2')

    def test_api_cannot_bypass_task_project_permissions(self):
        response = self.client.get('/api/tasks/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Private task')
        self.assertEqual(self.client.get('/api/tasks/tasks/%s/' % self.other_task.pk).status_code, 404)
        self.assertEqual(self.client.post('/api/tasks/tasks/', {'title':'API forged','project':self.other_project.pk,'status':'todo'}).status_code, 403)
        self.assertEqual(self.client.post('/api/tasks/subtasks/', {'title':'API forged','task':self.other_task.pk,'status':'todo'}).status_code, 403)
        self.assertEqual(self.client.post('/api/tasks/tasks/', {'title':'Bad assignee','project':self.project.pk,'status':'todo','u_users':[self.outsider.pk]}).status_code, 400)
        self.assertEqual(self.client.post('/api/tasks/subtasks/', {'title':'API valid','task':self.task.pk,'status':'todo'}).status_code, 201)
        self.client.force_login(self.customer)
        self.assertNotContains(self.client.get('/api/tasks/tasks/'), 'Visible task')
        for mode in ('1','2'):
            response = self.client.get(reverse('projects:project_list'), {'mode':mode})
            self.assertNotContains(response, 'Visible task')

    def test_ordinary_user_cannot_grant_admin_role_via_api(self):
        response = self.client.patch('/api/users/users/%s/' % self.owner.pk, data='{"is_superuser":true}', content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.is_superuser)
        response = self.client.post('/api/users/users/', {'username':'Elevated','email':'elevated@example.test','password':'test-only','is_superuser':True})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(get_user_model().objects.filter(username='Elevated').exists())
        self.owner.is_superuser = True; self.owner.save(update_fields=['is_superuser'])
        response = self.client.patch('/api/users/users/%s/' % self.member.pk, data='{"password":"new-test-password"}', content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password('new-test-password'))
