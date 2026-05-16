from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_admin() or user.is_viewer():
            return Project.objects.all()
        return Project.objects.filter(owner=user)

    def perform_create(self, serializer):
        if self.request.user.is_viewer():
            raise PermissionDenied("Viewers cannot create projects.")
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        project = self.get_object()
        if not self.request.user.is_admin() and project.owner != self.request.user:
            raise PermissionDenied("You can only edit your own projects.")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_admin() and instance.owner != self.request.user:
            raise PermissionDenied("You can only delete your own projects.")
        instance.delete()
