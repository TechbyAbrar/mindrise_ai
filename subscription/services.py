from datetime import timedelta
from decimal import Decimal
from typing import TypedDict, List

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from account.models import UserAuth
from .models import Subscription


class GrowthMetric(TypedDict):
    total: int | float
    growth_rate: float


class MonthlyStat(TypedDict):
    month: str
    total: int


def _month_range():
    now = timezone.now()
    this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    return this_month, last_month


def get_total_customers_with_growth() -> GrowthMetric:
    this_month, last_month = _month_range()

    total_customers: int = UserAuth.objects.only("user_id").count()

    current_month: int = UserAuth.objects.filter(
        date_joined__gte=this_month
    ).count()

    last_month_count: int = UserAuth.objects.filter(
        date_joined__gte=last_month,
        date_joined__lt=this_month,
    ).count()

    growth_rate: float = (
        ((current_month - last_month_count) / last_month_count) * 100
        if last_month_count
        else 0.0
    )

    return {
        "total": total_customers,
        "growth_rate": round(growth_rate, 2),
    }


def get_total_revenue_with_growth() -> GrowthMetric:
    this_month, last_month = _month_range()

    current: Decimal = (
        Subscription.objects.filter(created_at__gte=this_month)
        .aggregate(total=Sum("plan_price"))["total"]
        or Decimal("0.00")
    )

    previous: Decimal = (
        Subscription.objects.filter(created_at__gte=last_month, created_at__lt=this_month)
        .aggregate(total=Sum("plan_price"))["total"]
        or Decimal("0.00")
    )

    growth_rate: float = (
        float((current - previous) / previous * 100)
        if previous
        else 0.0
    )

    return {
        "total": float(current),
        "growth_rate": round(growth_rate, 2),
    }


def get_user_growth_monthly(limit: int = 12) -> List[MonthlyStat]:
    qs = (
        UserAuth.objects
        .annotate(month=TruncMonth("date_joined"))
        .values("month")
        .annotate(total=Count("user_id"))
        .order_by("month")[:limit]
    )

    return [
        {"month": item["month"].strftime("%Y-%m"), "total": item["total"]}
        for item in qs
    ]
