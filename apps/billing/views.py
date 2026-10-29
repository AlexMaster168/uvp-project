from apps.project_records import ProjectRecordMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
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


class BillingCreateView(LoginRequiredMixin, ProjectRecordMixin, CreateView):
    model = Billing
    form_class = BillingForm
    template_name = 'billing/billing_form.html'

    def get_initial(self):
        return {'project': self.request.GET.get('project')}

    def get_success_url(self):
        return super().get_success_url()


class BillingUpdateView(LoginRequiredMixin, ProjectRecordMixin, UpdateView):
    model = Billing
    form_class = BillingForm
    template_name = 'billing/billing_form.html'

    def get_success_url(self):
        return super().get_success_url()


class BillingDeleteView(LoginRequiredMixin, ProjectRecordMixin, DeleteView):
    model = Billing
    template_name = 'billing/billing_confirm_delete.html'

    def get_success_url(self):
        return super().get_success_url()


class BillingViewSet(viewsets.ModelViewSet):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project', 'operation', 'tag', 'date']
    ordering_fields = ['date', 'amount']
