from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import MediaFile
from .serializers import MediaFileSerializer

class MediaFileListView(LoginRequiredMixin, ListView):
    model = MediaFile
    template_name = 'media_files/mediafile_list.html'
    context_object_name = 'media_files'
    paginate_by = 20

class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project']
