from django.urls import path
from .views import OnboardingAPIView, TrackMoodListCreateAPIView, TrackMoodDetailAPIView, WeeklyMoodSummaryAPIView

urlpatterns = [
    path('create-details/', OnboardingAPIView.as_view(), name='onboarding'),
    
    path("moods/", TrackMoodListCreateAPIView.as_view(), name="mood-list-create"),
    path("moods/<int:pk>/", TrackMoodDetailAPIView.as_view(), name="mood-detail"),
    
    # last mood tracking api
    path("moods/weekly-summary/",WeeklyMoodSummaryAPIView.as_view(), name="weekly-mood-summary",),
]
