from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("id", "email", "display_name", "password")
        read_only_fields = ("id",)

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            display_name=validated_data.get("display_name", ""),
        )


class EncryptionSetupSerializer(serializers.Serializer):
    enc_verifier = serializers.CharField()
    enc_verifier_nonce = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    storage_used = serializers.IntegerField(read_only=True)
    has_encryption = serializers.SerializerMethodField()

    def get_has_encryption(self, obj):
        return bool(obj.enc_verifier)

    def validate_display_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Name is required.")
        if cleaned.lower() == "unnamed":
            raise serializers.ValidationError("“Unnamed” isn’t allowed — pick a real name.")
        if len(cleaned) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return cleaned

    class Meta:
        model = User
        fields = (
            "id", "email", "display_name", "kdf_salt", "kdf_iterations",
            "has_encryption", "enc_verifier", "enc_verifier_nonce",
            "storage_used", "storage_quota", "date_joined",
        )
        read_only_fields = (
            "id", "email", "kdf_salt", "kdf_iterations",
            "has_encryption", "enc_verifier", "enc_verifier_nonce",
            "storage_used", "storage_quota", "date_joined",
        )
