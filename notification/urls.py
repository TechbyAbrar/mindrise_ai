# notifications/urls.py
from django.urls import path
from .views import AdminNotificationListAPI, MarkNotificationReadAPI

urlpatterns = [
    path("admin/get-list/", AdminNotificationListAPI.as_view()),
    path("admin/get-info/<int:pk>/read/", MarkNotificationReadAPI.as_view()),
]
