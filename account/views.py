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
        

from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.db.models import Q

LOGIN_MAX_ATTEMPTS = 5      # max failed login attempts
LOGIN_BLOCK_SECONDS = 300   # block for 5 minutes if exceeded

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email_or_username = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")

        if not email_or_username or not password:
            return ResponseHandler.bad_request("Email/username and password are required")

        ip = self._get_ip(request)
        login_key = f"login:attempts:{ip}:{email_or_username}"

        # Safe increment: initialize key if not exists
        if cache.get(login_key) is None:
            cache.set(login_key, 0, timeout=LOGIN_BLOCK_SECONDS)

        if cache.get(login_key) >= LOGIN_MAX_ATTEMPTS:
            logger.warning("Blocked login attempt", extra={"ip": ip, "user": email_or_username})
            return ResponseHandler.error(
                f"Too many failed login attempts. Try again in {LOGIN_BLOCK_SECONDS // 60} minutes",
                status_code=429,
            )

        try:
            user = UserAuth.objects.only(
                "user_id", "email", "password", "is_active", "is_verified"
            ).get(Q(email__iexact=email_or_username) | Q(username__iexact=email_or_username) | Q(phone=email_or_username))
        except UserAuth.DoesNotExist:
            cache.incr(login_key)
            logger.warning("Failed login: user not found", extra={"ip": ip, "user": email_or_username})
            return ResponseHandler.unauthorized("Invalid credentials")

        if not user.is_active:
            return ResponseHandler.forbidden("User account inactive")
        if not user.is_verified:
            return ResponseHandler.forbidden("Email not verified")

        authenticated_user = authenticate(request, username=email_or_username, password=password)
        
        if not authenticated_user:
            cache.incr(login_key)
            logger.warning("Failed login: wrong password", extra={"user_id": user.user_id, "email": user.email, "ip": ip})
            return ResponseHandler.unauthorized("Invalid credentials")

        # Successful login
        cache.delete(login_key)
        with transaction.atomic():
            UserAuth.objects.filter(pk=user.user_id).update(last_login=timezone.now())
            user.refresh_from_db(fields=["last_login"])

        tokens = generate_tokens_for_user(user)
        logger.info("User login successful", extra={"user_id": user.user_id, "email": user.email, "ip": ip})

        return ResponseHandler.success(
            "Login successful",
            data={
                "user": UserSerializer(user).data,
                "tokens": tokens
            },
        )

    @staticmethod
    def _get_ip(request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")