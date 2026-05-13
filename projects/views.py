from django.shortcuts import render, redirect, get_object_or_404
from .models import Project
from .forms import ProjectForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@login_required
def project_list(request):
    ...

@login_required
def project_detail(request, pk):
    ...

@login_required
def project_list(request):
    if request.user.is_admin() or request.user.is_viewer():
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(owner=request.user)
    return render(request, 'projects/project_list.html', {'projects': projects})


@login_required
def project_create(request):
    if request.user.is_viewer():
        raise PermissionDenied
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            return redirect('projects:project_list')
    else:
        form = ProjectForm()
    return render(request, 'projects/project_form.html', {'form': form})


@login_required
def project_detail(request, pk):
    if request.user.is_admin() or request.user.is_viewer():
        project = get_object_or_404(Project, pk=pk)
    else:
        project = get_object_or_404(Project, pk=pk, owner=request.user)
    return render(request, 'projects/project_detail.html', {'project': project})

@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner != request.user:
        raise PermissionDenied
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'projects/project_form.html', {'form': form})

@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner != request.user:
        raise PermissionDenied
    if request.method == 'POST':
        project.delete()
        return redirect('projects:project_list')
    return render(request, 'projects/project_confirm_delete.html', {'project': project})
