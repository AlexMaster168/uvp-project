from django import forms
from .models import Access

class AccessForm(forms.ModelForm):
    class Meta:
        model = Access
        fields = ['project', 'url', 'url_drive', 'login', 'password', 'description', 'amount', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'