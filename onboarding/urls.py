from django.urls import path
from .views import OnboardingAPIView

urlpatterns = [
    path('create-details/', OnboardingAPIView.as_view(), name='onboarding'),
]
