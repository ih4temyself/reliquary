from django.http import FileResponse, Http404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.audit.services import record

from .models import File, Folder
from .serializers import FileSerializer, FileUploadSerializer, FolderSerializer


class FolderViewSet(viewsets.ModelViewSet):
    serializer_class = FolderSerializer

    def get_queryset(self):
        qs = Folder.objects.filter(owner=self.request.user)
        parent = self.request.query_params.get("parent")
        if parent == "root":
            qs = qs.filter(parent__isnull=True)
        elif parent:
            qs = qs.filter(parent_id=parent)
        return qs

    def perform_create(self, serializer):
        folder = serializer.save(owner=self.request.user)
        record(self.request, AuditLog.Action.FOLDER_CREATE, folder.id, folder.name)

    def perform_destroy(self, instance):
        record(self.request, AuditLog.Action.FOLDER_DELETE, instance.id, instance.name)
        instance.delete()


class FileViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action == "create":
            return FileUploadSerializer
        return FileSerializer

    def get_queryset(self):
        qs = File.objects.filter(owner=self.request.user)
        folder = self.request.query_params.get("folder")
        if folder == "root":
            qs = qs.filter(folder__isnull=True)
        elif folder:
            qs = qs.filter(folder_id=folder)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.save()
        record(request, AuditLog.Action.UPLOAD, file.id, file.name)
        return Response(FileSerializer(file, context=self.get_serializer_context()).data,
                        status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        record(self.request, AuditLog.Action.DELETE, instance.id, instance.name)
        instance.blob.delete(save=False)
        instance.delete()

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        file = self.get_object()
        try:
            handle = file.blob.open("rb")
        except FileNotFoundError:
            raise Http404("Encrypted blob is missing.")
        record(request, AuditLog.Action.DOWNLOAD, file.id, file.name)
        response = FileResponse(handle, content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{file.id}.enc"'
        response["X-File-Nonce"] = file.nonce
        return response
