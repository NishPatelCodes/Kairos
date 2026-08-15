from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.timeutils import user_today

from .models import Conversation
from .serializers import ConversationSerializer


def get_or_create_today(user, kind: str = "daily") -> Conversation:
    day = user_today(user)
    convo, _ = Conversation.objects.get_or_create(user=user, date=day, kind=kind)
    return convo


class TodayConversationView(APIView):
    def get(self, request):
        profile = getattr(request.user, "profile", None)
        kind = "onboarding" if profile and not profile.onboarding_completed else "daily"
        convo = get_or_create_today(request.user, kind=kind)
        return Response(ConversationSerializer(convo).data)
