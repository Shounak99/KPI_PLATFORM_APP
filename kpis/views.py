from django.shortcuts import render, redirect, get_object_or_404
from projects.models import Project
from .models import KPI
from .forms import KPIForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def project_list(request):
    ...

@login_required
def project_detail(request, pk):
    ...

@login_required
def kpi_create(request, project_pk):
    if request.user.is_viewer():
        raise PermissionDenied
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == 'POST':
        form = KPIForm(request.POST)
        if form.is_valid():
            kpi = form.save(commit=False)
            kpi.project = project
            kpi.save()
            messages.success(request, 'KPI created successfully.')
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = KPIForm()
    return render(request, 'kpis/kpi_form.html', {'form': form, 'project': project})

@login_required
def kpi_edit(request, project_pk, pk):
    if request.user.is_viewer():
        raise PermissionDenied
    project = get_object_or_404(Project, pk=project_pk)
    kpi = get_object_or_404(KPI, pk=pk, project=project)
    if request.method == 'POST':
        form = KPIForm(request.POST, instance=kpi)
        if form.is_valid():
            form.save()
            messages.success(request, 'KPI updated successfully.')
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = KPIForm(instance=kpi)
    return render(request, 'kpis/kpi_form.html', {'form': form, 'project': project})

@login_required
def kpi_delete(request, project_pk, pk):
    if request.user.is_viewer():
        raise PermissionDenied
    project = get_object_or_404(Project, pk=project_pk)
    kpi = get_object_or_404(KPI, pk=pk, project=project)
    if request.method == 'POST':
        kpi.delete()
        messages.success(request, 'KPI deleted.')
        return redirect('projects:project_detail', pk=project.pk)
    return render(request, 'kpis/kpi_confirm_delete.html', {'kpi': kpi, 'project': project})

