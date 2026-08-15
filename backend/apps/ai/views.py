import json

from django.http import StreamingHttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.conversations.serializers import ConversationSerializer
from apps.conversations.views import get_or_create_today

from .orchestrator import orchestrator


def _sse(event: str, data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n".encode("utf-8")


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = (request.data.get("message") or "").strip()
        if not text:
            return Response({"detail": "Message is required."}, status=400)

        profile = getattr(request.user, "profile", None)
        kind = "onboarding" if profile and not profile.onboarding_completed else "daily"
        conversation = get_or_create_today(request.user, kind=kind)

        def stream():
            for payload in orchestrator.stream_reply(request.user, conversation, text):
                yield _sse(payload["event"], payload["data"])

        response = StreamingHttpResponse(stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class StartupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        convo = orchestrator.ensure_opener(request.user)
        return Response(ConversationSerializer(convo).data)
