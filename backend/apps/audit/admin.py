from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "target_name", "ip_address", "created_at")
    list_filter = ("action",)
    search_fields = ("target_name",)
    readonly_fields = ("id", "user", "action", "target_id", "target_name", "ip_address", "created_at")
