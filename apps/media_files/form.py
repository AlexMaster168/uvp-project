from django import forms
from .models import MediaFile

class MediaFileForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['project', 'file', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'