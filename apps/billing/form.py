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
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
