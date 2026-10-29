from django import forms
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Task, SubTask
from apps.projects.models import Project
from .access import task_projects
from config.jinja2 import _

User = get_user_model()


class TaskForm(forms.ModelForm):
    initial_subtasks = forms.CharField(required=False, max_length=15000, label='Додати підзадачі', widget=forms.Textarea(attrs={'rows': 3}))
    time_unit = forms.ChoiceField(
        choices=[('hours', 'Години'), ('days', 'Людино-дні (8 годин)')],
        initial='hours', required=False, label='Одиниця часу',
    )
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'estimated_time', 'actual_time', 'project', 'u_users', 'u_tags']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [(value, _(label)) for value, label in Task.STATUS_CHOICES]
        self.fields['project'].queryset = task_projects(user) if user is not None else Project.objects.all()
        self.fields['project'].widget.attrs['class'] = 'form-select'
        if self.instance.pk:
            self.fields['project'].disabled = True
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['u_users'].widget.attrs['class'] = 'form-select'
        self.fields['u_tags'].widget.attrs['class'] = 'form-select'
        self.fields['time_unit'].widget.attrs['class'] = 'form-select'
        self.fields['project'].widget.attrs['class'] = 'form-select'

        project_id = None
        if self.is_bound and not self.instance.pk and self.data.get('project'):
            project_id = self.data.get('project')
        elif self.instance.pk and self.instance.project:
            project_id = self.instance.project.id
        elif 'project' in self.initial:
            project_id = self.initial['project']
        elif self.data.get('project'):
            project_id = self.data.get('project')

        if project_id:
            try:
                allowed = self.fields['project'].queryset.filter(pk=project_id).exists()
                self.fields['u_users'].queryset = User.objects.filter(
                    Q(project_memberships__project_id=project_id) |
                    Q(id__in=Project.objects.filter(pk=project_id).values('u_creator'))
                ).distinct() if allowed else User.objects.none()
            except (ValueError, TypeError, Project.DoesNotExist):
                self.fields['u_users'].queryset = User.objects.none()
        else:
            self.fields['u_users'].queryset = User.objects.none()

    def clean(self):
        data = super().clean()
        multiplier = 8 if data.get('time_unit') == 'days' else 1
        for name in ('estimated_time', 'actual_time'):
            value = data.get(name)
            if value is not None:
                if value < 0:
                    self.add_error(name, 'Час не може бути від’ємним.')
                else:
                    data[name] = value * multiplier
        return data

    def clean_initial_subtasks(self):
        titles = [line.strip() for line in self.cleaned_data.get('initial_subtasks', '').splitlines() if line.strip()]
        if len(titles) > 50 or any(len(title) > 255 for title in titles):
            raise forms.ValidationError('Не більше 50 підзадач, кожна назва — до 255 символів.')
        return titles


class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ['task', 'title', 'status', 'u_users']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [(value, _(label)) for value, label in Task.STATUS_CHOICES]
        self.fields['task'].queryset = Task.objects.filter(project__in=task_projects(user))
        self.fields['task'].required = True
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['task'].widget.attrs['class'] = 'form-select'
        if self.instance.pk:
            self.fields['task'].disabled = True
        task_id = self.instance.task_id if self.instance.pk else self.data.get('task') if self.is_bound else self.initial.get('task')
        try:
            task = self.fields['task'].queryset.get(pk=task_id)
        except (Task.DoesNotExist, ValueError, TypeError):
            self.fields['u_users'].queryset = User.objects.none()
        else:
            self.fields['u_users'].queryset = User.objects.filter(
                Q(project_memberships__project=task.project) | Q(pk=task.project.u_creator_id)
            ).distinct()
