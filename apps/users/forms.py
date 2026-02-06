from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from apps.projects.models import Project, ProjectMembership

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AddUserToProjectForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(), label="Проект",
                                     widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = ProjectMembership
        fields = ['project', 'role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
