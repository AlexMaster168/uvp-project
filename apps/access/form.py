from apps.project_records import record_projects
from django import forms
from .models import Access

class AccessForm(forms.ModelForm):
    class Meta:
        model = Access
        fields = ['project', 'url', 'url_drive', 'login', 'password', 'description', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'password': forms.PasswordInput(render_value=True, attrs={'autocomplete': 'new-password'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["project"].queryset = record_projects(user).order_by("name")
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'