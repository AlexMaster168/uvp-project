from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend

from .form import MediaFileForm
from .models import MediaFile
from .serializers import MediaFileSerializer


class MediaFileListView(LoginRequiredMixin, ListView):
    model = MediaFile
    template_name = 'media_files/mediafile_list.html'
    context_object_name = 'media_files'
    paginate_by = 20


class MediaFileCreateView(LoginRequiredMixin, CreateView):
    model = MediaFile
    form_class = MediaFileForm
    template_name = 'media_files/mediafile_form.html'

    def get_initial(self):
        return {'project': self.request.GET.get('project')}

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


class MediaFileDeleteView(LoginRequiredMixin, DeleteView):
    model = MediaFile
    template_name = 'media_files/mediafile_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project']
