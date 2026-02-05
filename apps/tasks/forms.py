from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'status', 'estimated_time', 'actual_time', 'project', 'u_users', 'u_tags']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['u_users'].widget.attrs['class'] = 'form-select'
        self.fields['u_tags'].widget.attrs['class'] = 'form-select'
