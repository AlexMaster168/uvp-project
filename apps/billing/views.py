from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .form import BillingForm
from .models import Billing
from .serializers import BillingSerializer


class BillingListView(LoginRequiredMixin, ListView):
    model = Billing
    template_name = 'billing/billing_list.html'
    context_object_name = 'billings'
    paginate_by = 20


class BillingCreateView(LoginRequiredMixin, CreateView):
    model = Billing
    form_class = BillingForm
    template_name = 'billing/billing_form.html'

    def get_initial(self):
        return {'project': self.request.GET.get('project')}

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


class BillingUpdateView(LoginRequiredMixin, UpdateView):
    model = Billing
    form_class = BillingForm
    template_name = 'billing/billing_form.html'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


class BillingDeleteView(LoginRequiredMixin, DeleteView):
    model = Billing
    template_name = 'billing/billing_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.project.pk})


class BillingViewSet(viewsets.ModelViewSet):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project', 'operation', 'tag', 'date']
    ordering_fields = ['date', 'amount']
