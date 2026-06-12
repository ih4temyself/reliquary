from .models import AuditLog


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record(request, action, target_id=None, target_name=""):
    return AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        target_id=target_id,
        target_name=target_name,
        ip_address=get_client_ip(request),
    )
