from django.conf import settings
from django.db import models


class ScheduleItem(models.Model):
    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("in_progress", "In progress"),
        ("completed", "Completed"),
        ("missed", "Missed"),
        ("rescheduled", "Rescheduled"),
    ]
    KIND_CHOICES = [
        ("focus", "Focus"),
        ("break", "Break"),
        ("fixed", "Fixed"),
        ("habit", "Habit"),
        ("flexible", "Flexible"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="schedule_items"
    )
    monthly_goal = models.ForeignKey(
        "goals.MonthlyGoal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="schedule_items",
    )
    title = models.CharField(max_length=280)
    notes = models.TextField(blank=True)
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="focus")
    is_fixed = models.BooleanField(default=False)
    created_by = models.CharField(max_length=10, default="ai")
    completed_at = models.DateTimeField(null=True, blank=True)
    original_start = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "start_time"]
        indexes = [
            models.Index(fields=["user", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.date} {self.start_time} {self.title}"

    @property
    def duration_minutes(self) -> int:
        start_m = self.start_time.hour * 60 + self.start_time.minute
        end_m = self.end_time.hour * 60 + self.end_time.minute
        return max(0, end_m - start_m)
