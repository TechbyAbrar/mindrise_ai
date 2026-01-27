from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import OnboardingSerializer, TrackMoodSerializer
from .services import OnboardingService, TrackMoodService
from .models import TrackMood
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count

class OnboardingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            onboarding = OnboardingService.get_onboarding(user=request.user)
        except ObjectDoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Onboarding not completed yet",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = OnboardingSerializer(onboarding)
        return Response(
            {
                "success": True,
                "message": "Onboarding details retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        onboarding, created = OnboardingService.upsert_onboarding(
            user=request.user,
            coaching_style=serializer.validated_data["coaching_style_id"],
            focus=serializer.validated_data.get("focus", []),
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Onboarding details created successfully"
                    if created
                    else "Onboarding details updated successfully"
                ),
                "data": OnboardingSerializer(onboarding).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class TrackMoodListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        moods = TrackMoodService.list(user=request.user)
        serializer = TrackMoodSerializer(moods, many=True)
        return Response({
            'success': True,
            'message': 'Mood entries retrieved successfully',
            'data': serializer.data
        })

    def post(self, request):
        serializer = TrackMoodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mood = TrackMoodService.create(
            user=request.user,
            data=serializer.validated_data
        )

        return Response({
            'success': True,
            'message': 'Mood entry created successfully',
            'data':TrackMoodSerializer(mood).data},
            status=status.HTTP_201_CREATED
        )

class TrackMoodDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        mood = TrackMoodService.get(user=request.user, mood_id=pk)
        serializer = TrackMoodSerializer(mood)
        return Response({
            'success': True,
            'message': 'Mood entry retrieved successfully',
            'data': serializer.data
        })

    def put(self, request, pk):
        mood = TrackMoodService.get(user=request.user, mood_id=pk)

        serializer = TrackMoodSerializer(mood, data=request.data)
        serializer.is_valid(raise_exception=True)

        mood = TrackMoodService.update(
            instance=mood,
            data=serializer.validated_data
        )

        return Response({
            'success': True,
            'message': 'Mood entry updated successfully',
            'data': TrackMoodSerializer(mood).data
        })

    def delete(self, request, pk):
        mood = TrackMoodService.get(user=request.user, mood_id=pk)
        TrackMoodService.delete(instance=mood)
        return Response({
            'success': True,
            'message': 'Mood entry deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


class WeeklyMoodSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = now().date()
        week_start = today - timedelta(days=6)

        # Last mood entry
        last_mood = (
            TrackMood.objects
            .filter(user=user)
            .order_by("-mood_date")
            .first()
        )

        last_mood_data = (
            TrackMoodSerializer(last_mood).data if last_mood else None
        )

        # Weekly check-ins
        weekly_qs = TrackMood.objects.filter(
            user=user,
            mood_date__range=[week_start, today]
        )

        checked_in_days = weekly_qs.count()

        # Weekly mood statistics
        mood_counts = (
            weekly_qs
            .values("mood_score")
            .annotate(total=Count("id"))
        )

        mood_map = dict(TrackMood.MOOD_CHOICES)
        weekly_mood_stats = {
            mood_map[item["mood_score"]]: item["total"]
            for item in mood_counts
        }

        return Response({
            "success": True,
            "message": "Weekly mood summary retrieved successfully",
            "last_checkin": last_mood_data,
            "weekly_checkins": {
                "checked_in_days": checked_in_days,
                "total_days": 7,
                "missed_days": 7 - checked_in_days
            },
            "weekly_mood_stats": weekly_mood_stats
        })