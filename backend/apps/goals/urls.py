from django.urls import path

from .views import (
    AnnualGoalDetailView,
    AnnualGoalListCreateView,
    MonthlyGoalDetailView,
    MonthlyGoalListCreateView,
)

urlpatterns = [
    path("annual/", AnnualGoalListCreateView.as_view()),
    path("annual/<int:pk>/", AnnualGoalDetailView.as_view()),
    path("monthly/", MonthlyGoalListCreateView.as_view()),
    path("monthly/<int:pk>/", MonthlyGoalDetailView.as_view()),
]
