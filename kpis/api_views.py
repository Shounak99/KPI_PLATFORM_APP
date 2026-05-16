from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from projects.models import Project
from .models import KPI
from .serializers import KPISerializer


class KPIViewSet(viewsets.ModelViewSet):
    serializer_class = KPISerializer

    def get_queryset(self):
        return KPI.objects.filter(project_id=self.kwargs['project_pk'])

    def perform_create(self, serializer):
        if self.request.user.is_viewer():
            raise PermissionDenied("Viewers cannot create KPIs.")
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        serializer.save(project=project)
