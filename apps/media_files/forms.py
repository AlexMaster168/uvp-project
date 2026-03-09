from django import forms
from .models import MediaFile


class MediaFileForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['project', 'file', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'file': forms.FileInput(
                attrs={'class': 'form-control image-crop-input', 'data-preview-target': '#media-preview',
                       'accept': 'image/*'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'initial' in kwargs and 'project' in kwargs['initial']:
            self.fields['project'].widget = forms.HiddenInput()
