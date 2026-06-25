import base64
import os
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

KDF_DEFAULT_ITERATIONS = 600_000
DEFAULT_STORAGE_QUOTA = 15 * 1024 * 1024 * 1024


def generate_kdf_salt():
    return base64.b64encode(os.urandom(16)).decode()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=150, blank=True)
    kdf_salt = models.CharField(max_length=64, default=generate_kdf_salt, editable=False)
    kdf_iterations = models.PositiveIntegerField(default=KDF_DEFAULT_ITERATIONS)
    enc_verifier = models.TextField(blank=True, default="")
    enc_verifier_nonce = models.CharField(max_length=64, blank=True, default="")
    storage_quota = models.BigIntegerField(default=DEFAULT_STORAGE_QUOTA)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def storage_used(self):
        from django.db.models import Sum

        from apps.files.models import File

        return File.objects.filter(owner=self).aggregate(total=Sum("encrypted_size"))["total"] or 0
