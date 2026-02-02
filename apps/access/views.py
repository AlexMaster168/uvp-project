from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Access
from .serializers import AccessSerializer

class AccessListView(LoginRequiredMixin, ListView):
    model = Access
    template_name = 'access/access_list.html'
    context_object_name = 'accesses'
    paginate_by = 20

class AccessViewSet(viewsets.ModelViewSet):
    queryset = Access.objects.all()
    serializer_class = AccessSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['project']
    search_fields = ['login', 'url', 'description']
