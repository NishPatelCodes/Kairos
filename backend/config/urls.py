from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    return JsonResponse({"ok": True, "name": "kairos"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/goals/", include("apps.goals.urls")),
    path("api/schedule/", include("apps.schedule.urls")),
    path("api/conversations/", include("apps.conversations.urls")),
    path("api/ai/", include("apps.ai.urls")),
    path("api/progress/", include("apps.progress.urls")),
]
