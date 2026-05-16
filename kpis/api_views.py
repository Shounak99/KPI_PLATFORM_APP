from rest_framework import viewsets, generics
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q
from projects.models import Project
from .models import KPI
from .serializers import KPISerializer, KPIListSerializer


class KPIViewSet(viewsets.ModelViewSet):
    serializer_class = KPISerializer

    def get_queryset(self):
        return KPI.objects.filter(project_id=self.kwargs['project_pk'])

    def perform_create(self, serializer):
        if self.request.user.is_viewer():
            raise PermissionDenied("Viewers cannot create KPIs.")
        project = get_object_or_404(Project, pk=self.kwargs['project_pk'])
        serializer.save(project=project)


class AllKPIsView(generics.ListAPIView):
    serializer_class = KPIListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_project_owner():
            queryset = KPI.objects.filter(project__owner=user)
        else:
            queryset = KPI.objects.all()

        queryset = queryset.select_related('project')

        search = self.request.query_params.get('search', '').strip()
        status = self.request.query_params.get('status', '').strip()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(project__name__icontains=search)
            )
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('project__name', 'name')
