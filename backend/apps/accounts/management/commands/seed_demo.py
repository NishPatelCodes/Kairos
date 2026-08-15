from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import date, time

from apps.accounts.models import UserPreference, UserProfile
from apps.goals.models import AnnualGoal, MonthlyGoal
from apps.schedule.models import ScheduleItem


class Command(BaseCommand):
    help = "Create a demo user with sample goals. Development only."

    def handle(self, *args, **options):
        email = "demo@kairos.app"
        user, created = User.objects.get_or_create(
            username=email,
            defaults={"email": email, "first_name": "Demo"},
        )
        if created:
            user.set_password("demo12345")
            user.save()
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "display_name": "Demo",
                "timezone": "America/Halifax",
                "onboarding_completed": True,
                "peak_energy": "morning",
                "typical_weekday": "Deep work 9–12, job in the afternoon, gym after work.",
            },
        )
        profile.onboarding_completed = True
        profile.save()
        prefs, _ = UserPreference.objects.get_or_create(user=user)
        prefs.work_start = time(8, 0)
        prefs.work_end = time(21, 0)
        prefs.preferred_block_minutes = 90
        prefs.save()

        today = date.today()
        year_end = date(today.year + 1, today.month, min(today.day, 28))
        AnnualGoal.objects.filter(user=user, is_active=True).update(is_active=False)
        annual = AnnualGoal.objects.create(
            user=user,
            title="Become a strong software engineer and land a high-quality SWE internship in Canada.",
            target_date=year_end,
            is_active=True,
        )
        month = today.replace(day=1)
        MonthlyGoal.objects.filter(user=user, month=month).delete()
        goals = [
            MonthlyGoal.objects.create(
                user=user,
                annual_goal=annual,
                title="Finish Meta Backend course",
                metric_target=8,
                metric_current=3,
                metric_unit="modules",
                month=month,
                priority=1,
            ),
            MonthlyGoal.objects.create(
                user=user,
                annual_goal=annual,
                title="Solve 50 LeetCode problems",
                metric_target=50,
                metric_current=18,
                metric_unit="problems",
                month=month,
                priority=2,
            ),
            MonthlyGoal.objects.create(
                user=user,
                annual_goal=annual,
                title="Build Businalyst MVP",
                metric_target=1,
                metric_current=0,
                metric_unit="milestone",
                month=month,
                priority=3,
            ),
        ]
        ScheduleItem.objects.filter(user=user, date=today).delete()
        ScheduleItem.objects.create(
            user=user,
            monthly_goal=goals[0],
            title="Django authentication module",
            date=today,
            start_time=time(9, 0),
            end_time=time(11, 0),
            kind="focus",
            status="upcoming",
            created_by="user",
        )
        ScheduleItem.objects.create(
            user=user,
            monthly_goal=goals[1],
            title="LeetCode — 2 problems",
            date=today,
            start_time=time(11, 0),
            end_time=time(11, 45),
            kind="focus",
            status="upcoming",
            created_by="ai",
        )
        ScheduleItem.objects.create(
            user=user,
            title="Lunch",
            date=today,
            start_time=time(12, 0),
            end_time=time(13, 0),
            kind="break",
            is_fixed=True,
            status="upcoming",
            created_by="user",
        )
        self.stdout.write(self.style.SUCCESS(f"Demo user ready: {email} / demo12345"))
