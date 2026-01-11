from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db import transaction

from .serializers import SignupSerializer, UserSerializer, VerifyOTPSerializer
from .services import send_otp_email, generate_tokens_for_user, generate_otp
from .utils import get_otp_expiry
from .response_handler import ResponseHandler  # Use class directly
from .models import UserAuth

from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.db.models import Q

import logging
logger = logging.getLogger(__name__)

class SignupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # DRF handles ValidationError natively

        with transaction.atomic():
            user = serializer.save()

            otp = generate_otp()
            user.set_otp(otp)

            send_otp_email(user.email, otp)

            # Generate tokens
            tokens = generate_tokens_for_user(user)

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
        

LOGIN_MAX_ATTEMPTS = 5     
LOGIN_BLOCK_SECONDS = 300  

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
    
    
# ----- Rate limiting config -----
FORGET_MAX_PER_HOUR = 10
FORGET_COOLDOWN_SECONDS = 60  

class ForgetPasswordView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("email", "").strip().lower()
        
        if not identifier:
            return ResponseHandler.bad_request("Email, phone, or username is required")

        cooldown_key = f"forget:cooldown:{identifier}"
        hourly_key = f"forget:hour:{identifier}"

        if cache.get(cooldown_key):
            return ResponseHandler.error( 
                "Please wait before requesting another password reset",
                status_code=429,
            )

        hourly_count = cache.get(hourly_key, 0)
        if hourly_count >= FORGET_MAX_PER_HOUR:
            return ResponseHandler.error(
                "Password reset limit exceeded. Try again later.",
                status_code=429,
            )

        try:
            user = UserAuth.objects.only("user_id", "email", "is_active", "is_verified").get(
                Q(email__iexact=identifier) |
                Q(username__iexact=identifier) |
                Q(phone=identifier)
            )
        except UserAuth.DoesNotExist:
            self._set_limits(identifier)
            return ResponseHandler.success(
                "If the account exists, a password reset OTP has been sent"
            )

        if not user.is_active or not user.is_verified:
            self._set_limits(identifier)
            return ResponseHandler.success(
                "If the account exists, a password reset OTP has been sent"
            )

        otp = generate_otp()
        otp_expiry = get_otp_expiry(minutes=30)

        try:
            with transaction.atomic():
                user.otp = otp
                user.otp_expired_at = otp_expiry
                user.save(update_fields=["otp", "otp_expired_at"])
                self._set_limits(identifier)
        except Exception:
            logger.exception("Error saving OTP", extra={"user_id": user.user_id})
            return ResponseHandler.server_error("Unable to process request. Try later.")

        if not send_otp_email(user.email, otp):
            logger.error("Failed to send OTP email", extra={"user_id": user.user_id})
            return ResponseHandler.success(
                "If the account exists, a password reset OTP has been sent"
            )

        logger.info(
            "Password reset OTP sent",
            extra={"user_id": user.user_id, "email": user.email},
        )

        return ResponseHandler.success(
            "If the account exists, a password reset OTP has been sent"
        )

    def _set_limits(self, identifier: str) -> None:
        cache.set(f"forget:cooldown:{identifier}", 1, timeout=FORGET_COOLDOWN_SECONDS)
        cache.set(
            f"forget:hour:{identifier}",
            cache.get(f"forget:hour:{identifier}", 0) + 1,
            timeout=3600,
        )
        
        
        
        