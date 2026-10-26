from django import forms
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Task
from apps.projects.models import Project

User = get_user_model()


class TaskForm(forms.ModelForm):
    time_unit = forms.ChoiceField(
        choices=[('hours', 'Години'), ('days', 'Людино-дні (8 годин)')],
        initial='hours', required=False, label='Одиниця часу',
    )
    class Meta:
        model = Task
        fields = ['title', 'status', 'estimated_time', 'actual_time', 'project', 'u_users', 'u_tags']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['u_users'].widget.attrs['class'] = 'form-select'
        self.fields['u_tags'].widget.attrs['class'] = 'form-select'
        self.fields['time_unit'].widget.attrs['class'] = 'form-select'

        project_id = None
        if self.instance.pk and self.instance.project:
            project_id = self.instance.project.id
        elif 'project' in self.initial:
            project_id = self.initial['project']
        elif self.data.get('project'):
            project_id = self.data.get('project')

        if project_id:
            try:
                self.fields['u_users'].queryset = User.objects.filter(
                    Q(project_memberships__project_id=project_id) |
                    Q(id__in=Project.objects.filter(pk=project_id).values('u_creator'))
                ).distinct()
            except (ValueError, Project.DoesNotExist):
                pass
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
