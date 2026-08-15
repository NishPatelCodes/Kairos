from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.timeutils import user_today
from apps.schedule.engine import parse_date

from .services import daily_progress, monthly_progress, weekly_progress


class DailyProgressView(APIView):
    def get(self, request):
        day = parse_date(request.query_params.get("date"), request.user)
        return Response(daily_progress(request.user, day))


class WeeklyProgressView(APIView):
    def get(self, request):
        return Response(weekly_progress(request.user))


class MonthlyProgressView(APIView):
    def get(self, request):
        return Response(monthly_progress(request.user))


class DashboardView(APIView):
    def get(self, request):
        user = request.user
        today = user_today(user)
        daily = daily_progress(user, today)
        weekly = weekly_progress(user, today)
        monthly = monthly_progress(user, today)
        return Response(
            {
                "daily": daily,
                "weekly": weekly,
                "monthly": monthly,
            }
        )
