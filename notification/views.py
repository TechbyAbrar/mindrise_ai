
# notifications/apis.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status

from django.shortcuts import get_object_or_404
from django.db.models import QuerySet
from typing import List

from .models import Notification
from .serializers import NotificationSerializer

class AdminNotificationListAPI(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request) -> Response:
        qs: QuerySet[Notification] = Notification.objects.only(
            "id", "event", "title", "message", "user_id", "is_read", "created_at"
        )[:50]

        data: List[dict] = NotificationSerializer(qs, many=True).data
        return Response({"success": True, "data": data})


# notifications/apis.py

class MarkNotificationReadAPI(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk: int) -> Response:
        notif = get_object_or_404(Notification, pk=pk)
        notif.is_read = True
        notif.save(update_fields=["is_read"])

        return Response({"success": True}, status=status.HTTP_200_OK)
