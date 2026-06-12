from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AuditLogViewSet, DashboardView

app_name = "audit"

router = DefaultRouter()
router.register("logs", AuditLogViewSet, basename="auditlog")

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
] + router.urls
