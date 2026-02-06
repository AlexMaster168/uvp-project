from django import forms
from .models import Project, Tag


class ProjectForm(forms.ModelForm):
    new_tags = forms.CharField(
        required=False,
        label='Создать новые теги',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите теги через запятую (например: python, backend, api)'
        })
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date', 'status', 'logo', 'u_tags']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'u_tags': forms.SelectMultiple(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

        self.fields['u_tags'].queryset = Tag.objects.all()
        self.fields['u_tags'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()

            new_tags_input = self.cleaned_data.get('new_tags')
            if new_tags_input:
                names = [n.strip() for n in new_tags_input.split(',') if n.strip()]
                for name in names:
                    tag, _ = Tag.objects.get_or_create(name=name)
                    instance.u_tags.add(tag)
        return instance
