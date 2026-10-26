from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.tasks.models import Task, SubTask
from .models import Project, ProjectMembership
from .reporting import management_report


class ManagementReportTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='owner', email='owner@example.test', password='test-only')
        self.project = Project.objects.create(name='Report <safe>', u_creator=self.owner,
                                              end_date=timezone.localdate() - timedelta(days=1))
        self.client.force_login(self.owner)
        self.url = reverse('projects:project_detail', kwargs={'pk': self.project.pk})

    def test_remaining_work_and_risk(self):
        other = get_user_model().objects.create_user(username='other', email='other@example.test')
        task = Task.objects.create(project=self.project, title='Work', estimated_time=24, actual_time=8)
        task.u_users.add(self.owner, other)
        SubTask.objects.create(task=task, title='Done', status='done')
        SubTask.objects.create(task=task, title='Open')
        Task.objects.create(project=self.project, title='Overrun', estimated_time=8, actual_time=10)
        report = management_report(self.project)
        self.assertEqual(report['remaining_days'], 2)
        self.assertEqual(dict(report['workload']), {'owner': 1, 'other': 1})
        self.assertEqual(report['risks'], 1)
        self.assertEqual(report['progress'], 33)
        self.assertEqual(report['overdue_days'], 1)

    def test_completed_task_and_unknown_estimate(self):
        task = Task.objects.create(project=self.project, title='Completed', status='done', estimated_time=80)
        SubTask.objects.create(task=task, title='Old state')
        report = management_report(self.project)
        self.assertEqual(report['progress'], 100)
        self.assertEqual(report['pending'], 0)
        self.assertEqual(report['remaining_days'], 0)
        Task.objects.create(project=self.project, title='Unknown')
        self.assertEqual(management_report(self.project)['unestimated'], 1)

    def test_modes_render_and_escape_titles(self):
        for mode in ('1', '3', '4'):
            response = self.client.get(self.url, {'mode': mode})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'data-mode="4"')
            self.assertContains(response, 'Report &lt;safe&gt;')
        response = self.client.get(self.url, {'mode': '4'})
        self.assertContains(response, 'У проєкті ще немає задач.')

    def test_both_report_layouts_show_tasks(self):
        Task.objects.create(project=self.project, title='Important <task>', estimated_time=8, actual_time=9)
        for mode in ('3', '4'):
            response = self.client.get(self.url, {'mode': mode})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Important &lt;task&gt;')
            self.assertContains(response, 'report-risk')
        self.assertContains(self.client.get(self.url, {'mode': '3'}), 'compact-progress')

    def test_nonmember_cannot_view_report(self):
        outsider = get_user_model().objects.create_user(username='outsider', email='outsider@example.test')
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(self.url, {'mode': '4'}).status_code, 404)

    def test_customer_receives_summary_only(self):
        customer = get_user_model().objects.create_user(username='customer', email='customer@example.test')
        ProjectMembership.objects.create(project=self.project, user=customer, role='customer')
        Task.objects.create(project=self.project, title='Internal task')
        self.client.force_login(customer)
        response = self.client.get(self.url, {'mode': '4'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Internal task')

    def test_project_list_all_modes_and_permissions(self):
        outsider = get_user_model().objects.create_user(username='outsider', email='other@example.test')
        hidden = Project.objects.create(name='Private outsider project', u_creator=outsider)
        Task.objects.create(project=self.project, title='Budget risk', estimated_time=8, actual_time=9)
        for mode in ('1', '2', '3', '4'):
            response = self.client.get(reverse('projects:project_list'), {'mode': mode})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'data-list-mode="4"')
            self.assertContains(response, 'Report &lt;safe&gt;')
            self.assertNotContains(response, hidden.name)
            if mode in ('3', '4'):
                self.assertContains(response, 'data-report-project="%s"' % self.project.pk)
                self.assertEqual(response.context_data['project_reports'][0]['report']['risks'], 1)

    def test_list_filter_and_pagination_keep_mode(self):
        Project.objects.bulk_create([
            Project(name='Portfolio & report %s' % i, u_creator=self.owner, status='in_progress')
            for i in range(21)
        ])
        response = self.client.get(reverse('projects:project_list'), {
            'mode': '4', 'q': 'Portfolio & report', 'status': 'in_progress',
        })
        self.assertEqual(response.status_code, 200)
        params = parse_qs(urlparse(response.context_data['next_page_url']).query)
        self.assertEqual(params['mode'], ['4'])
        self.assertEqual(params['q'], ['Portfolio & report'])
        self.assertEqual(params['status'], ['in_progress'])
        self.assertEqual(len(response.context_data['project_reports']), 20)
        self.assertNotContains(response, 'Report &lt;safe&gt;')
