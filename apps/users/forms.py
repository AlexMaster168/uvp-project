from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from apps.projects.models import Project, ProjectMembership
from .models import GlobalSettings

User = get_user_model()


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Email or Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'you@example.com or username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022',
            'id': 'password-input',
        })
    )

    def clean(self):
        identifier = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if identifier and password:
            from django.contrib.auth import authenticate
            self.user_cache = authenticate(
                self.request,
                username=identifier,
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'avatar']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(
                attrs={'class': 'form-control image-crop-input', 'data-preview-target': '#avatar-preview'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'avatar']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control bg-light border-0 py-2'}),
            'email': forms.EmailInput(attrs={'class': 'form-control bg-light border-0 py-2'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control bg-light border-0 py-2'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control bg-light border-0 py-2'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control bg-light border-0 py-2 image-crop-input',
                                             'data-preview-target': '#avatar-preview'}),
        }


class AddUserToProjectForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset=Project.objects.all(),
                                     widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = ProjectMembership
        fields = ['project', 'role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }


class GlobalSettingsForm(forms.ModelForm):
    class Meta:
        model = GlobalSettings
        fields = ['theme', 'language']
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
        }
