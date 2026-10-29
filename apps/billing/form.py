from apps.project_records import record_projects
from django import forms
from .models import Billing


class BillingForm(forms.ModelForm):
    class Meta:
        model = Billing
        fields = ['project', 'date', 'amount', 'description', 'tag', 'operation', 'users']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["project"].queryset = record_projects(user).order_by("name")
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
