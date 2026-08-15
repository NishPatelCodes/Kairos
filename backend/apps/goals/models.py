from django.conf import settings
from django.db import models


class AnnualGoal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="annual_goals"
    )
    title = models.CharField(max_length=280)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "-created_at"]

    def __str__(self) -> str:
        return self.title


class MonthlyGoal(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("paused", "Paused"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="monthly_goals"
    )
    annual_goal = models.ForeignKey(
        AnnualGoal, on_delete=models.SET_NULL, null=True, blank=True, related_name="monthly_goals"
    )
    title = models.CharField(max_length=280)
    description = models.TextField(blank=True)
    metric_target = models.FloatField(null=True, blank=True)
    metric_current = models.FloatField(default=0)
    metric_unit = models.CharField(max_length=80, blank=True)
    month = models.DateField(help_text="First day of the month this goal belongs to.")
    priority = models.PositiveSmallIntegerField(default=3)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "id"]

    def __str__(self) -> str:
        return self.title

    @property
    def progress_pct(self) -> float | None:
        if not self.metric_target:
            return None
        return round(min(100.0, (self.metric_current / self.metric_target) * 100), 1)
