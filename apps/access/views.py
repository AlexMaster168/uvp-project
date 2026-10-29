from apps.project_records import ProjectRecordMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .form import AccessForm
from .models import Access
from .serializers import AccessSerializer


class AccessListView(LoginRequiredMixin, ListView):
    model = Access
    template_name = 'access/access_list.html'
    context_object_name = 'accesses'
    paginate_by = 20


class AccessCreateView(LoginRequiredMixin, ProjectRecordMixin, CreateView):
    model = Access
    form_class = AccessForm
    template_name = 'access/access_form.html'

    def get_initial(self):
        return {'project': self.request.GET.get('project')}

    def get_success_url(self):
        return super().get_success_url()


class AccessUpdateView(LoginRequiredMixin, ProjectRecordMixin, UpdateView):
    model = Access
    form_class = AccessForm
    template_name = 'access/access_form.html'

    def get_success_url(self):
        return super().get_success_url()


class AccessDeleteView(LoginRequiredMixin, ProjectRecordMixin, DeleteView):
    model = Access
    template_name = 'access/access_confirm_delete.html'

    def get_success_url(self):
        return super().get_success_url()


class AccessViewSet(viewsets.ModelViewSet):
    queryset = Access.objects.all()
    serializer_class = AccessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project']
    search_fields = ['login', 'url', 'description']
