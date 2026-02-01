from django.urls import path
from .views import UserInformationList, DashboardMetricsAPIView

urlpatterns = [
    path('users/list/', UserInformationList.as_view(), name='user-subscription-list'),
    path("dashboard/metrics/", DashboardMetricsAPIView.as_view(), name="dashboard-metrics"),
]
