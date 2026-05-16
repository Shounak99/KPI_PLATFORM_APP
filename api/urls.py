from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from projects.api_views import ProjectViewSet
from kpis.api_views import KPIViewSet
from accounts.api_views import RegisterView, me_view

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

kpi_list = KPIViewSet.as_view({'get': 'list', 'post': 'create'})
kpi_detail = KPIViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})

urlpatterns = router.urls + [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', me_view, name='me'),
    path('projects/<int:project_pk>/kpis/', kpi_list, name='project-kpis-list'),
    path('projects/<int:project_pk>/kpis/<int:pk>/', kpi_detail, name='project-kpis-detail'),
]
