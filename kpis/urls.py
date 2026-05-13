from django.urls import path
from . import views

app_name = 'kpis'

urlpatterns = [path('new/', views.kpi_create, name='kpi_create'),
                path('<int:pk>/edit/', views.kpi_edit, name='kpi_edit'),
                path('<int:pk>/delete/', views.kpi_delete, name='kpi_delete'),
]
