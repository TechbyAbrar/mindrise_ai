# urls.py
from django.urls import path
from .views import CreateOnboardingAPIView, GetOnboardingAPIView

urlpatterns = [
    path("create/", CreateOnboardingAPIView.as_view(), name="create-onboarding"),
    path("details/<str:coaching_style>/", GetOnboardingAPIView.as_view(), name="get-onboarding"),
]
