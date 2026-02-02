from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Billing
from .serializers import BillingSerializer

class BillingListView(LoginRequiredMixin, ListView):
    model = Billing
    template_name = 'billing/billing_list.html'
    context_object_name = 'billings'
    paginate_by = 20

class BillingViewSet(viewsets.ModelViewSet):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['project', 'operation', 'tag', 'date']
    ordering_fields = ['date', 'amount']
