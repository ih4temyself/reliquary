import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        UPLOAD = "upload", "Upload"
        DOWNLOAD = "download", "Download"
        DELETE = "delete", "Delete"
        MOVE = "move", "Move"
        FOLDER_CREATE = "folder_create", "Folder created"
        FOLDER_DELETE = "folder_delete", "Folder deleted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    target_id = models.UUIDField(null=True, blank=True)
    target_name = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self):
        return f"{self.action} {self.target_name}"
