from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, parsers

from .models import MediaFile
from .forms import MediaFileForm
from .serializers import MediaFileSerializer
from apps.projects.models import Project


class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)


class MediaCreateView(LoginRequiredMixin, CreateView):
    model = MediaFile
    form_class = MediaFileForm
    template_name = 'media_files/mediafile_form.html'

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.request.GET.get('project')
        if project_id:
            initial['project'] = get_object_or_404(Project, pk=project_id)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.request.GET.get('project')
        if project_id:
            context['project'] = get_object_or_404(Project, pk=project_id)
        return context

    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.object.project.pk}) + '#media'


class MediaUpdateView(LoginRequiredMixin, UpdateView):
    model = MediaFile
    form_class = MediaFileForm
    template_name = 'media_files/mediafile_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.object.project
        return context

    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.object.project.pk}) + '#media'


class MediaDeleteView(LoginRequiredMixin, DeleteView):
    model = MediaFile
    template_name = 'media_files/mediafile_confirm_delete.html'

    def get_success_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.object.project.pk}) + '#media'
