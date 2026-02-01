from django.db.models import F
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import UserAuth

from .services import (
    get_total_customers_with_growth,
    get_total_revenue_with_growth,
    get_user_growth_monthly,
)

# Create your views here.
def get_users_with_subscription():
    return (
        UserAuth.objects
        .select_related("subscription")
        .annotate(plan_name=F("subscription__plan_name"))
        .values(
            "full_name",
            "username",
            "email",
            "profile_pic",
            "date_joined",
            "plan_name",
        )
    )

class UserInformationList(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        data = list(get_users_with_subscription())
        return Response({
            "success": True,
            "message": "User data fetched successfully",
            "data": data
        })


class DashboardMetricsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    data = {
                "customers": get_total_customers_with_growth(),
                "revenue": get_total_revenue_with_growth(),
                "user_growth": get_user_growth_monthly(),
            }

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "Dashboard metrics fetched successfully",
                "data": self.data,
            }
        )
