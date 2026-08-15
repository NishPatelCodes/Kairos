from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ENERGY_CHOICES = [
        ("morning", "Morning"),
        ("afternoon", "Afternoon"),
        ("evening", "Evening"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    display_name = models.CharField(max_length=120, blank=True)
    timezone = models.CharField(max_length=64, default="America/Halifax")
    onboarding_completed = models.BooleanField(default=False)
    peak_energy = models.CharField(max_length=20, choices=ENERGY_CHOICES, default="morning")
    typical_weekday = models.TextField(blank=True)
    blockers = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.display_name or self.user.username


class UserPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences"
    )
    work_start = models.TimeField(null=True, blank=True)
    work_end = models.TimeField(null=True, blank=True)
    preferred_block_minutes = models.PositiveIntegerField(default=90)
    break_every_minutes = models.PositiveIntegerField(default=120)
    break_duration_minutes = models.PositiveIntegerField(default=15)
    updated_at = models.DateTimeField(auto_now=True)
