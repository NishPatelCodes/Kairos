from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserPreference, UserProfile
from .serializers import ProfileSerializer, RegisterSerializer


def tokens_for(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        profile = user.profile
        return Response(
            {
                **tokens_for(user),
                "user": ProfileSerializer(profile).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").lower().strip()
        password = request.data.get("password") or ""
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({"detail": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)
        UserProfile.objects.get_or_create(
            user=user,
            defaults={"display_name": user.first_name or email.split("@")[0]},
        )
        UserPreference.objects.get_or_create(user=user)
        return Response(
            {
                **tokens_for(user),
                "user": ProfileSerializer(user.profile).data,
            }
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"display_name": self.request.user.first_name or self.request.user.username},
        )
        UserPreference.objects.get_or_create(user=self.request.user)
        return profile
