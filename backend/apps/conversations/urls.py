from django.urls import path

from .views import TodayConversationView

urlpatterns = [
    path("today/", TodayConversationView.as_view()),
]
