from django.contrib import admin
from .models import Billing

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ['project', 'date', 'amount', 'operation', 'tag']
    list_filter = ['operation', 'tag', 'date']
    search_fields = ['description', 'project__name']
    filter_horizontal = ['users']
