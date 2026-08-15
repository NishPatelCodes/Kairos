from django.contrib import admin

from .models import ScheduleItem


@admin.register(ScheduleItem)
class ScheduleItemAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "date", "start_time", "end_time", "status")
    list_filter = ("status", "kind")
