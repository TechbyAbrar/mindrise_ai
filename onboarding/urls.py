from django.urls import path
from .views import OnboardingAPIView, TrackMoodListCreateAPIView, TrackMoodDetailAPIView

urlpatterns = [
    path('create-details/', OnboardingAPIView.as_view(), name='onboarding'),
    
    path("moods/", TrackMoodListCreateAPIView.as_view(), name="mood-list-create"),
    path("moods/<int:pk>/", TrackMoodDetailAPIView.as_view(), name="mood-detail"),
]
