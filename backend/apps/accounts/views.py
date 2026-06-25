import json
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import EncryptionSetupSerializer, RegisterSerializer, UserSerializer

User = get_user_model()

TOKENINFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            return Response({"detail": "Google sign-in is not configured."}, status=503)

        access_token = request.data.get("access_token")
        if not access_token:
            return Response({"detail": "access_token is required."}, status=400)

        try:
            url = f"{TOKENINFO_URL}?{urllib.parse.urlencode({'access_token': access_token})}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                info = json.loads(resp.read())
        except Exception:
            return Response({"detail": "Could not verify Google token."}, status=401)

        if info.get("aud") != settings.GOOGLE_OAUTH_CLIENT_ID:
            return Response({"detail": "Token was not issued for this app."}, status=401)
        if str(info.get("email_verified")).lower() != "true":
            return Response({"detail": "Google email is not verified."}, status=401)

        email = info.get("email", "").lower()
        if not email:
            return Response({"detail": "Google token has no email."}, status=401)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"display_name": info.get("name", "")[:150]},
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])

        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})


class EncryptionSetupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.enc_verifier:
            return Response(
                {"detail": "Encryption passphrase is already set."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = EncryptionSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.enc_verifier = serializer.validated_data["enc_verifier"]
        request.user.enc_verifier_nonce = serializer.validated_data["enc_verifier_nonce"]
        request.user.save(update_fields=["enc_verifier", "enc_verifier_nonce"])
        return Response(UserSerializer(request.user).data)
