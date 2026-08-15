from django.contrib import admin

from .models import AnnualGoal, MonthlyGoal


@admin.register(AnnualGoal)
class AnnualGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "target_date", "is_active")


@admin.register(MonthlyGoal)
class MonthlyGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "month", "priority", "status")
