from django.contrib import admin
from .models import KPI

@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'status', 'actual_value', 'target_value']
    list_filter = ['status']
    search_fields = ['name', 'project__name']
