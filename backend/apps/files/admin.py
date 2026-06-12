from django.contrib import admin

from .models import File, Folder


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "parent", "created_at")
    search_fields = ("name",)
    raw_id_fields = ("owner", "parent")


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "folder", "encrypted_size", "created_at")
    search_fields = ("name",)
    raw_id_fields = ("owner", "folder")
