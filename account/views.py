from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import transaction

from .serializers import SignupSerializer, UserSerializer, VerifyOTPSerializer
from .utils import generate_otp
from .services import send_otp_email, generate_tokens_for_user
from .response_handler import ResponseHandler  # Use class directly


class SignupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # DRF handles ValidationError natively

        with transaction.atomic():
            user = serializer.save()

            # Generate and set OTP
            otp = generate_otp()
            user.set_otp(otp)

            # Send OTP email
            send_otp_email(user.email, otp)

            # Generate tokens
            tokens = generate_tokens_for_user(user)

            # Return consistent response
            return ResponseHandler.created(
                message="User created successfully. OTP sent to email.",
                data={
                    "user": UserSerializer(user).data,
                    "access_tokens": tokens["access"],
                },
            )


class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Validation handled natively
        serializer.save()

        return ResponseHandler.success(
            message="Email verified successfully."
        )
