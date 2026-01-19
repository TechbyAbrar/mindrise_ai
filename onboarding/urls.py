# urls.py
from django.urls import path
from .views import CreateOnboardingAPIView, GetOnboardingAPIView

urlpatterns = [
    path("onboarding/", CreateOnboardingAPIView.as_view(), name="create-onboarding"),
    path("onboarding/<str:coaching_style>/", GetOnboardingAPIView.as_view(), name="get-onboarding"),
]
