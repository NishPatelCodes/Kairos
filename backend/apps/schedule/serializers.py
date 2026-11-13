from rest_framework import serializers

from .engine import parse_time
from .models import ScheduleItem


class ScheduleItemSerializer(serializers.ModelSerializer):
    duration_minutes = serializers.IntegerField(read_only=True)
    goal_title = serializers.CharField(source="monthly_goal.title", read_only=True, default=None)
    goal_metric_unit = serializers.CharField(source="monthly_goal.metric_unit", read_only=True, default=None)
    goal_metric_target = serializers.FloatField(source="monthly_goal.metric_target", read_only=True, default=None)
    goal_metric_current = serializers.FloatField(source="monthly_goal.metric_current", read_only=True, default=None)

    class Meta:
        model = ScheduleItem
        fields = (
            "id",
            "monthly_goal",
            "goal_title",
            "goal_metric_unit",
            "goal_metric_target",
            "goal_metric_current",
            "title",
            "notes",
            "date",
            "start_time",
            "end_time",
            "status",
            "kind",
            "is_fixed",
            "created_by",
            "completed_at",
            "duration_minutes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "completed_at",
            "created_at",
            "updated_at",
            "duration_minutes",
            "goal_title",
            "goal_metric_unit",
            "goal_metric_target",
            "goal_metric_current",
        )

    def validate(self, attrs):
        start = attrs.get("start_time") or getattr(self.instance, "start_time", None)
        end = attrs.get("end_time") or getattr(self.instance, "end_time", None)
        if start and end and end <= start:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})
        return attrs


def serialize_item(item: ScheduleItem) -> dict:
    return ScheduleItemSerializer(item).data
