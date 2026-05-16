from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    kpi_count = serializers.IntegerField(source='kpis.count', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    on_track = serializers.SerializerMethodField()
    at_risk = serializers.SerializerMethodField()
    off_track = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'owner_username', 'kpi_count',
                  'on_track', 'at_risk', 'off_track', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_on_track(self, obj):
        return obj.kpis.filter(status='on_track').count()

    def get_at_risk(self, obj):
        return obj.kpis.filter(status='at_risk').count()

    def get_off_track(self, obj):
        return obj.kpis.filter(status='off_track').count()
