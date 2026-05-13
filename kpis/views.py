from django.shortcuts import render, redirect, get_object_or_404
from projects.models import Project
from .models import KPI
from .forms import KPIForm

def kpi_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == 'POST':
        form = KPIForm(request.POST)
        if form.is_valid():
            kpi = form.save(commit=False)
            kpi.project = project
            kpi.save()
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = KPIForm()
    return render(request, 'kpis/kpi_form.html', {'form': form, 'project': project})


def kpi_edit(request, project_pk, pk):
    project = get_object_or_404(Project, pk=project_pk)
    kpi = get_object_or_404(KPI, pk=pk, project=project)
    if request.method == 'POST':
        form = KPIForm(request.POST, instance=kpi)
        if form.is_valid():
            form.save()
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = KPIForm(instance=kpi)
    return render(request, 'kpis/kpi_form.html', {'form': form, 'project': project})

def kpi_delete(request, project_pk, pk):
    project = get_object_or_404(Project, pk=project_pk)
    kpi = get_object_or_404(KPI, pk=pk, project=project)
    if request.method == 'POST':
        kpi.delete()
        return redirect('projects:project_detail', pk=project.pk)
    return render(request, 'kpis/kpi_confirm_delete.html', {'kpi': kpi, 'project': project})

