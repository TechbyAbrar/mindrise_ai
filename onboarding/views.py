# Standard library
from datetime import timedelta, datetime
from calendar import monthrange
# Django
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, Count
from django.utils import timezone
from django.utils.timezone import now

# Django REST Framework
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Local apps
from .models import TrackMood
from .serializers import OnboardingSerializer, TrackMoodSerializer
from .services import OnboardingService, TrackMoodService


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
        
        
# calculate streaks


from datetime import datetime, timedelta
from django.db.models import Avg
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import TrackMood


ISO_DATE_FORMAT = "%Y-%m-%d"


def parse_iso_date(value: str, field_name: str):
    if not value:
        raise ValidationError({
            field_name: "This field is required in ISO format YYYY-MM-DD."
        })
    try:
        return datetime.strptime(value, ISO_DATE_FORMAT).date()
    except ValueError:
        raise ValidationError({
            field_name: "Invalid date format. Expected YYYY-MM-DD."
        })


# class MoodReportAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         today = timezone.now().date()

#         range_param = request.query_params.get("range")
#         start_date_param = request.query_params.get("start_date")
#         end_date_param = request.query_params.get("end_date")

#         if range_param:
#             if not range_param.endswith("d") or not range_param[:-1].isdigit():
#                 return Response(
#                     {"range": "Invalid range format. Example: 7d, 30d"},
#                     status=400,
#                 )

#             days = int(range_param[:-1])
#             if days <= 0:
#                 return Response(
#                     {"range": "Range must be greater than 0 days."},
#                     status=400,
#                 )

#             end_date = today
#             start_date = end_date - timedelta(days=days - 1)

#         elif start_date_param or end_date_param:
#             if not (start_date_param and end_date_param):
#                 return Response(
#                     {"error": "Both start_date and end_date are required."},
#                     status=400,
#                 )

#             start_date = parse_iso_date(start_date_param, "start_date")
#             end_date = parse_iso_date(end_date_param, "end_date")

#             if start_date > end_date:
#                 return Response(
#                     {"error": "start_date cannot be greater than end_date."},
#                     status=400,
#                 )

#         else:
#             return Response(
#                 {
#                     "error": (
#                         "Provide either ?range=7d "
#                         "OR ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD"
#                     )
#                 },
#                 status=400,
#             )

#         total_days = (end_date - start_date).days + 1
#         mood_qs = (
#             TrackMood.objects
#             .filter(
#                 user=user,
#                 mood_date__range=(start_date, end_date)
#             )
#             .values("mood_date")
#             .annotate(avg_mood=Avg("mood_score"))
#         )

#         mood_map = {
#             row["mood_date"]: round(row["avg_mood"], 2)
#             for row in mood_qs
#         }

#         mood_history = [
#             {
#                 "date": d,
#                 "day": d.strftime("%a").upper(),
#                 "avg_mood": mood_map.get(d, None),  # change to -1 if needed
#             }
#             for d in (
#                 start_date + timedelta(days=i)
#                 for i in range(total_days)
#             )
#         ]

#         mood_dates = set(mood_map.keys())
#         current_streak = 0
#         check_date = end_date

#         while check_date in mood_dates:
#             current_streak += 1
#             check_date -= timedelta(days=1)

#         last_mood_date = end_date if end_date in mood_dates else None

#         active_days = sorted(d.day for d in mood_dates)

#         return Response({
#             "range": {
#                 "start_date": start_date,
#                 "end_date": end_date,
#                 "total_days": total_days,
#             },
#             "streak": {
#                 "current_days": current_streak,
#                 "last_mood_date": last_mood_date,
#             },
#             "mood_history": mood_history,
#             "activity_log": {
#                 "active_days": active_days,
#             },
#         })
class MoodReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        range_param = request.query_params.get("range")
        start_date_param = request.query_params.get("start_date")
        end_date_param = request.query_params.get("end_date")

        if range_param:
            if not range_param.endswith("d") or not range_param[:-1].isdigit():
                return Response(
                    {"range": "Invalid range format. Example: 7d, 30d"},
                    status=400,
                )

            days = int(range_param[:-1])
            if days <= 0:
                return Response({"range": "Range must be greater than 0 days."}, status=400)

            end_date = today
            start_date = end_date - timedelta(days=days - 1)

        elif start_date_param or end_date_param:
            if not (start_date_param and end_date_param):
                return Response(
                    {"error": "Both start_date and end_date are required."},
                    status=400,
                )

            start_date = parse_iso_date(start_date_param, "start_date")
            end_date = parse_iso_date(end_date_param, "end_date")

            if start_date > end_date:
                return Response(
                    {"error": "start_date cannot be greater than end_date."},
                    status=400,
                )

        else:
            return Response(
                {
                    "error": (
                        "Provide either ?range=7d "
                        "OR ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD"
                    )
                },
                status=400,
            )

        total_days = (end_date - start_date).days + 1

        mood_qs = (
            TrackMood.objects
            .filter(
                user=user,
                mood_date__range=(start_date, end_date),
            )
            .values("mood_date")
            .annotate(avg_mood=Avg("mood_score"))
        )

        # Build map safely (avg_mood will NEVER be null if a row exists)
        mood_map = {
            row["mood_date"]: float(round(row["avg_mood"], 2))
            for row in mood_qs
            if row["avg_mood"] is not None
        }

        mood_history = []
        for i in range(total_days):
            d = start_date + timedelta(days=i)
            mood_history.append({
                "date": d.isoformat(),
                "day": d.strftime("%a").upper(),
                "avg_mood": mood_map.get(d),  # None only if no entry exists
            })

        mood_dates = sorted(mood_map.keys())

        # ✅ FIXED STREAK LOGIC
        current_streak = 0
        last_mood_date = None

        if mood_dates:
            last_mood_date = max(mood_dates)
            check_date = last_mood_date

            while check_date in mood_map:
                current_streak += 1
                check_date -= timedelta(days=1)

        active_days = [d.day for d in mood_dates]

        return Response({
            "range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_days": total_days,
            },
            "streak": {
                "current_days": current_streak,
                "last_mood_date": last_mood_date.isoformat() if last_mood_date else None,
            },
            "mood_history": mood_history,
            "activity_log": {
                "active_days": active_days,
            },
        })
