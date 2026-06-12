from django.db.models import Count, Sum
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.files.models import File, Folder

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.filter(user=self.request.user)
        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)
        date_from = self.request.query_params.get("from")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        date_to = self.request.query_params.get("to")
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs


class DashboardView(APIView):
    def get(self, request):
        files = File.objects.filter(owner=request.user)
        stats = files.aggregate(count=Count("id"), total_size=Sum("encrypted_size"))
        recent = AuditLog.objects.filter(user=request.user)[:10]
        return Response({
            "file_count": stats["count"] or 0,
            "total_size": stats["total_size"] or 0,
            "folder_count": Folder.objects.filter(owner=request.user).count(),
            "recent_activity": AuditLogSerializer(recent, many=True).data,
        })
