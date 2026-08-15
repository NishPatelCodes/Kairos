from django.urls import path

from .views import CompleteScheduleView, MoveScheduleView, ScheduleDetailView, ScheduleListCreateView

urlpatterns = [
    path("", ScheduleListCreateView.as_view()),
    path("<int:pk>/", ScheduleDetailView.as_view()),
    path("<int:pk>/complete/", CompleteScheduleView.as_view()),
    path("<int:pk>/move/", MoveScheduleView.as_view()),
]
