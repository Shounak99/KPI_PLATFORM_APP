from rest_framework import serializers
from .models import KPI

class KPISerializer(serializers.ModelSerializer):
    progress_percent = serializers.FloatField(read_only=True)
    suggested_status = serializers.CharField(read_only=True)

    class Meta:
        model = KPI
        fields = ['id', 'project', 'name', 'description', 'unit',
                  'target_value', 'actual_value', 'status',
                  'progress_percent', 'suggested_status',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'project', 'created_at', 'updated_at']
