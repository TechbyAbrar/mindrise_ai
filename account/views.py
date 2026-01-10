from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import transaction

from .serializers import SignupSerializer, UserSerializer, VerifyOTPSerializer
from .services import send_otp_email, generate_tokens_for_user, generate_otp
from .utils import get_otp_expiry
from .response_handler import ResponseHandler  # Use class directly
from .models import UserAuth

import logging
logger = logging.getLogger(__name__)

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


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get("email")

        if not email:
            return ResponseHandler.bad_request("Email is required")

        email = email.strip().lower()

        try:
            user = UserAuth.objects.only(
                "user_id", "email", "is_active", "is_verified"
            ).get(email=email)
        except UserAuth.DoesNotExist:
            return ResponseHandler.not_found("User not found")

        if not user.is_active:
            return ResponseHandler.forbidden("User account inactive")

        if user.is_verified:
            return ResponseHandler.bad_request("User already verified")

        otp = generate_otp()
        expires_at = get_otp_expiry()  # ← reuse your utility

        # Single, cheap DB write
        with transaction.atomic():
            UserAuth.objects.filter(pk=user.pk).update(
                otp=otp,
                otp_expired_at=expires_at,
            )

        if not send_otp_email(user.email, otp):
            logger.error(
                "OTP email failed",
                extra={"user_id": user.pk, "email": user.email},
            )
            return ResponseHandler.server_error(
                "OTP generated but email failed"
            )

        logger.info(
            "OTP resent (admin)",
            extra={
                "user_id": user.pk,
                "email": user.email,
                "otp": otp,
            },
        )

        return ResponseHandler.success(
            "OTP resent successfully",
            data={
                "email": user.email,
                "otp": otp,
                "expires_at": expires_at,
            },
        )