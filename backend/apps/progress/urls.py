from django.urls import path

from .views import DailyProgressView, DashboardView, MonthlyProgressView, WeeklyProgressView

urlpatterns = [
    path("daily/", DailyProgressView.as_view()),
    path("weekly/", WeeklyProgressView.as_view()),
    path("monthly/", MonthlyProgressView.as_view()),
    path("dashboard/", DashboardView.as_view()),
]
