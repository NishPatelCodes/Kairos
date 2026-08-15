from django.urls import path

from .views import ChatView, StartupView

urlpatterns = [
    path("chat/", ChatView.as_view()),
    path("startup/", StartupView.as_view()),
]
