from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.schedule.engine import engine, parse_date, parse_time
from apps.schedule.serializers import ScheduleItemSerializer


class ScheduleListCreateView(APIView):
    def get(self, request):
        day = parse_date(request.query_params.get("date"), request.user)
        items = engine.for_day(request.user, day)
        return Response(ScheduleItemSerializer(items, many=True).data)

    def post(self, request):
        data = request.data
        item = engine.create(
            request.user,
            title=data.get("title"),
            day=parse_date(data.get("date"), request.user),
            start=parse_time(str(data.get("start_time"))),
            end=parse_time(str(data.get("end_time"))),
            monthly_goal_id=data.get("monthly_goal"),
            notes=data.get("notes") or "",
            kind=data.get("kind") or "focus",
            is_fixed=bool(data.get("is_fixed")),
            created_by="user",
        )
        return Response(ScheduleItemSerializer(item).data, status=status.HTTP_201_CREATED)


class ScheduleDetailView(APIView):
    def patch(self, request, pk: int):
        item = engine.update(request.user, pk, **request.data)
        return Response(ScheduleItemSerializer(item).data)

    def delete(self, request, pk: int):
        engine.delete(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompleteScheduleView(APIView):
    def post(self, request, pk: int):
        amount = request.data.get("progress_amount") if isinstance(request.data, dict) else None
        goal_id = request.data.get("goal_id") if isinstance(request.data, dict) else None
        if amount is not None and amount != "":
            amount = float(amount)
        else:
            amount = None
        if goal_id not in (None, ""):
            goal_id = int(goal_id)
        else:
            goal_id = None
        item = engine.complete(request.user, pk, progress_amount=amount, goal_id=goal_id)
        return Response(ScheduleItemSerializer(item).data)


class MoveScheduleView(APIView):
    def post(self, request, pk: int):
        item = engine.move(
            request.user,
            pk,
            start=parse_time(str(request.data.get("start_time"))),
            end=parse_time(str(request.data.get("end_time"))),
            day=parse_date(request.data.get("date"), request.user) if request.data.get("date") else None,
        )
        return Response(ScheduleItemSerializer(item).data)
