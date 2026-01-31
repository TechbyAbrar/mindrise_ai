from account.models import UserAuth
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

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
