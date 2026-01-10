from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from .serializers import SignupSerializer, UserSerializer, VerifyOTPSerializer
from .utils import generate_otp
from .services import send_otp_email, generate_tokens_for_user
from .response_handler import created_response, server_error_response, success_response
from django.db import transaction

class SignupAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                user = serializer.save()  # Persist user

                # Generate OTP and save
                otp = generate_otp()
                user.set_otp(otp)  # sets OTP and expiry

                # Send OTP via email (service layer)
                send_otp_email(user.email, otp)

                # Generate JWT tokens
                tokens = generate_tokens_for_user(user)

                return created_response(
                    message="User created successfully. OTP sent to email.",
                    data={
                        "user": UserSerializer(user).data,
                        "access_tokens": tokens['access'],
                    }
                )

        except Exception as exc:
            # Use minimal server error response
            return server_error_response(message="Signup failed.", errors=str(exc))


class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            message="Email verified successfully."
        )
