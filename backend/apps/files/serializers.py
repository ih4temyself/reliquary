from django.conf import settings
from django.db.models import Sum
from rest_framework import serializers

from .models import File, Folder


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ("id", "name", "parent", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_parent(self, value):
        if value is not None and value.owner_id != self.context["request"].user.id:
            raise serializers.ValidationError("Parent folder not found.")
        return value


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = (
            "id", "name", "content_type", "folder", "nonce",
            "encrypted_size", "created_at", "updated_at",
        )
        read_only_fields = ("id", "encrypted_size", "created_at", "updated_at")

    def validate_folder(self, value):
        if value is not None and value.owner_id != self.context["request"].user.id:
            raise serializers.ValidationError("Folder not found.")
        return value


class FileUploadSerializer(serializers.ModelSerializer):
    blob = serializers.FileField(write_only=True)

    class Meta:
        model = File
        fields = ("id", "name", "content_type", "folder", "nonce", "blob")
        read_only_fields = ("id",)

    def validate_blob(self, value):
        if value.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f"Encrypted file exceeds the maximum size of {settings.MAX_UPLOAD_SIZE} bytes."
            )
        return value

    def validate_folder(self, value):
        if value is not None and value.owner_id != self.context["request"].user.id:
            raise serializers.ValidationError("Folder not found.")
        return value

    def validate(self, attrs):
        blob = attrs.get("blob")
        user = self.context["request"].user
        used = File.objects.filter(owner=user).aggregate(total=Sum("encrypted_size"))["total"] or 0
        if blob and used + blob.size > user.storage_quota:
            remaining = max(user.storage_quota - used, 0)
            raise serializers.ValidationError(
                {"blob": f"Storage quota exceeded. {remaining} bytes remaining."}
            )
        return attrs

    def create(self, validated_data):
        blob = validated_data.pop("blob")
        return File.objects.create(
            owner=self.context["request"].user,
            blob=blob,
            encrypted_size=blob.size,
            **validated_data,
        )
