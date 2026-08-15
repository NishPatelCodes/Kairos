from rest_framework import serializers

from .models import AnnualGoal, MonthlyGoal


class AnnualGoalSerializer(serializers.ModelSerializer):
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = AnnualGoal
        fields = (
            "id",
            "title",
            "description",
            "target_date",
            "is_active",
            "days_remaining",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_days_remaining(self, obj: AnnualGoal) -> int:
        from apps.common.timeutils import user_today

        request = self.context.get("request")
        today = user_today(request.user) if request else obj.target_date
        return (obj.target_date - today).days

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        if validated_data.get("is_active"):
            AnnualGoal.objects.filter(user=validated_data["user"], is_active=True).update(is_active=False)
        return super().create(validated_data)


class MonthlyGoalSerializer(serializers.ModelSerializer):
    progress_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = MonthlyGoal
        fields = (
            "id",
            "annual_goal",
            "title",
            "description",
            "metric_target",
            "metric_current",
            "metric_unit",
            "month",
            "priority",
            "status",
            "progress_pct",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "progress_pct")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
