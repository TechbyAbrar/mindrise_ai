from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import OnboardingSerializer
from .services import OnboardingService
from .models import CoachingStyle

class OnboardingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            onboarding = OnboardingService.get_onboarding(user)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = OnboardingSerializer(onboarding)
        return Response({
            "success": True,
            "message": "Onboarding details retrieved successfully",
            "data": serializer.data,
        })

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        # The validated data now has "coaching_style_id" key
        coaching_style_obj = serializer.validated_data["coaching_style_id"]

        try:
            onboarding = OnboardingService.create_onboarding(
                user=user,
                coaching_style=coaching_style_obj,
                focus=serializer.validated_data.get("focus", [])
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)

        serializer = OnboardingSerializer(onboarding)
        return Response({
            "success": True,
            "message": "Onboarding details created successfully",
            "data": serializer.data,
        }, status=status.HTTP_201_CREATED)


