from django import forms
from .models import KPI

class KPIForm(forms.ModelForm):
    class Meta:
        model = KPI
        fields = ['name', 'description', 'unit', 'target_value', 'actual_value', 'status']
