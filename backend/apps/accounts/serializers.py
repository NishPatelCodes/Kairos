from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserPreference, UserProfile


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    display_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=64, required=False, default="America/Halifax")

    def validate_email(self, value: str) -> str:
        email = value.lower().strip()
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data["password"],
            first_name=validated_data.get("display_name", ""),
        )
        UserProfile.objects.create(
            user=user,
            display_name=validated_data.get("display_name", "") or email.split("@")[0],
            timezone=validated_data.get("timezone") or "America/Halifax",
        )
        UserPreference.objects.create(user=user)
        return user


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = (
            "work_start",
            "work_end",
            "preferred_block_minutes",
            "break_every_minutes",
            "break_duration_minutes",
        )


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    preferences = PreferenceSerializer(source="user.preferences", read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "email",
            "display_name",
            "timezone",
            "onboarding_completed",
            "peak_energy",
            "typical_weekday",
            "blockers",
            "preferences",
        )

    def update(self, instance, validated_data):
        prefs_payload = None
        if hasattr(self, "initial_data"):
            prefs_payload = self.initial_data.get("preferences")
        validated_data.pop("user", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if isinstance(prefs_payload, dict):
            prefs, _ = UserPreference.objects.get_or_create(user=instance.user)
            serializer = PreferenceSerializer(prefs, data=prefs_payload, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return instance
