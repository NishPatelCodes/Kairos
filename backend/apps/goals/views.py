from rest_framework import generics

from .models import AnnualGoal, MonthlyGoal
from .serializers import AnnualGoalSerializer, MonthlyGoalSerializer


class AnnualGoalListCreateView(generics.ListCreateAPIView):
    serializer_class = AnnualGoalSerializer

    def get_queryset(self):
        return AnnualGoal.objects.filter(user=self.request.user)


class AnnualGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AnnualGoalSerializer

    def get_queryset(self):
        return AnnualGoal.objects.filter(user=self.request.user)


class MonthlyGoalListCreateView(generics.ListCreateAPIView):
    serializer_class = MonthlyGoalSerializer

    def get_queryset(self):
        qs = MonthlyGoal.objects.filter(user=self.request.user)
        month = self.request.query_params.get("month")
        if month:
            qs = qs.filter(month=month)
        return qs


class MonthlyGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MonthlyGoalSerializer

    def get_queryset(self):
        return MonthlyGoal.objects.filter(user=self.request.user)
