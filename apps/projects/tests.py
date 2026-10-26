from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.tasks.models import Task, SubTask
from .models import Project, ProjectMembership
from .reporting import management_report
from .presentation import PROJECT_LIST_MODES, REPORT_TASK_LAYOUTS, project_list_mode


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
        for mode, _, kind in PROJECT_LIST_MODES:
            response = self.client.get(reverse('projects:project_list'), {'mode': mode})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'data-list-mode="4"')
            self.assertContains(response, 'Report &lt;safe&gt;')
            self.assertNotContains(response, hidden.name)
            if kind != 'cards':
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

    def test_each_personalization_control_has_a_visible_section(self):
        class Classes(HTMLParser):
            def __init__(self):
                super().__init__()
                self.classes = set()

            def handle_starttag(self, tag, attrs):
                self.classes.update(dict(attrs).get('class', '').split())

        for mode, _, _ in PROJECT_LIST_MODES:
            response = self.client.get(reverse('projects:project_list'), {'mode': mode})
            parser = Classes()
            parser.feed(response.content.decode())
            for control_id, _, target, _ in response.context_data['list_controls']:
                self.assertIn(target[1:], parser.classes, (mode, control_id))
            self.assertContains(response, 'id="projectTheme"')

    def test_finance_for_management_views(self):
        from apps.billing.models import Billing
        Billing.objects.create(project=self.project, amount=100, operation='income', date=timezone.localdate(), tag='actual_income')
        Billing.objects.create(project=self.project, amount=25, operation='expense', date=timezone.localdate(), tag='actual_expense')
        response = self.client.get(reverse('projects:project_list'), {'mode': '5'})
        finance = response.context_data['project_reports'][0]['finance']
        self.assertEqual(finance['income'], 100)
        self.assertEqual(finance['expense'], 25)

    def test_board_grouping_and_unknown_mode(self):
        response = self.client.get(reverse('projects:project_list'), {'mode': '6'})
        groups = {status: items for status, _, items in response.context_data['project_columns']}
        self.assertEqual(len(groups[self.project.status]), 1)
        self.assertEqual(sum(len(items) for items in groups.values()), 1)
        self.assertEqual(project_list_mode('unknown')[0], '1')

    def test_medusa_layout_selector_and_customer_access(self):
        Task.objects.create(project=self.project, title='Internal task')
        response = self.client.get(self.url, {'mode': '5'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Internal task')
        for value, label in REPORT_TASK_LAYOUTS:
            self.assertContains(response, 'value="%s"' % value)
            self.assertContains(response, label)
        customer = get_user_model().objects.create_user(username='customer', email='customer@example.test')
        ProjectMembership.objects.create(project=self.project, user=customer, role='customer')
        self.client.force_login(customer)
        for mode in ('3', '4', '5', '6', '7'):
            response = self.client.get(reverse('projects:project_list'), {'mode': mode})
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'Internal task')
        response = self.client.get(self.url, {'mode': '6'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Internal task')

    def test_project_view_dropdown(self):
        response = self.client.get(self.url, {'mode': '6'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="projectModeSelect"')
        self.assertContains(response, '<option data-mode=', count=6)

    def test_task_form_days_conversion_and_report(self):
        from apps.tasks.forms import TaskForm
        form = TaskForm(data={
            'title': 'Day estimate', 'status': 'in_progress', 'project': self.project.pk,
            'time_unit': 'days', 'estimated_time': '2.5', 'actual_time': '0.75',
        })
        self.assertTrue(form.is_valid(), form.errors)
        task = form.save()
        self.assertEqual(task.estimated_time, 20)
        self.assertEqual(task.actual_time, 6)
        report = management_report(self.project)
        self.assertEqual(report['planned_days'], 2.5)
        self.assertEqual(report['spent_days'], 0.75)
        self.assertEqual(report['remaining_days'], 1.75)
        self.assertEqual(report['rows'][0]['planned_days'], 2.5)

    def test_task_form_legacy_hours_and_negative_values(self):
        from apps.tasks.forms import TaskForm
        data = {'title': 'Hours', 'status': 'todo', 'project': self.project.pk,
                'estimated_time': '16', 'actual_time': '4'}
        form = TaskForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        task = form.save()
        self.assertEqual(task.estimated_time, 16)
        self.assertEqual(task.actual_time, 4)
        form = TaskForm(data={**data, 'time_unit': 'days', 'actual_time': '-1'})
        self.assertFalse(form.is_valid())
        self.assertIn('actual_time', form.errors)

    def test_completed_task_days_keep_actual_time(self):
        Task.objects.create(project=self.project, title='Done', status='done', estimated_time=8, actual_time=16)
        report = management_report(self.project)
        self.assertEqual(report['planned_days'], 1)
        self.assertEqual(report['spent_days'], 2)
        self.assertEqual(report['remaining_days'], 0)
