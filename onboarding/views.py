# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import OnboardingSerializer
from .services import OnboardingService

class CreateOnboardingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        try:
            onboarding = OnboardingService.create_onboarding(
                user_id=user.user_id,
                coaching_style=serializer.validated_data["coaching_style"],
                focus=serializer.validated_data.get("focus", [])
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response({
            "id": onboarding.id,
            "coaching_style": onboarding.coaching_style,
            "focus": onboarding.focus,
            "created_at": onboarding.created_at
        }, status=status.HTTP_201_CREATED)


class GetOnboardingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, coaching_style: str):
        user = request.user
        try:
            onboarding = OnboardingService.get_onboarding(user.user_id, coaching_style)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "id": onboarding.id,
            "coaching_style": onboarding.coaching_style,
            "focus": onboarding.focus,
            "created_at": onboarding.created_at,
            "updated_at": onboarding.updated_at
        })
