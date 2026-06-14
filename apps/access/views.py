from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
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


class AccessCreateView(LoginRequiredMixin, CreateView):
    model = Access
    form_class = AccessForm
    template_name = 'access/access_form.html'

    def get_initial(self):
        return {'project': self.request.GET.get('project')}

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


class AccessUpdateView(LoginRequiredMixin, UpdateView):
    model = Access
    form_class = AccessForm
    template_name = 'access/access_form.html'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


class AccessDeleteView(LoginRequiredMixin, DeleteView):
    model = Access
    template_name = 'access/access_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


class AccessViewSet(viewsets.ModelViewSet):
    queryset = Access.objects.all()
    serializer_class = AccessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project']
    search_fields = ['login', 'url', 'description']
