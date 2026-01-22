from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
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

from typing import Any
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password     
from .utils import decode_google_token, decode_apple_token
from typing import Dict, Optional    
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
        
        
  
class ForgetPasswordVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request: Any) -> Any:
        otp: str | None = request.data.get("otp")
        if not otp:
            return ResponseHandler.bad_request("OTP is required")

        try:
            user: UserAuth = UserAuth.objects.only(
                "user_id", "email", "otp", "otp_expired_at", "is_verified"
            ).get(otp=otp, is_verified=True)
        except UserAuth.DoesNotExist:
            return ResponseHandler.bad_request("Invalid or expired OTP")

        if not user.otp_expired_at or timezone.now() > user.otp_expired_at:
            return ResponseHandler.bad_request("OTP has expired")

        try:
            tokens: dict[str, str] = generate_tokens_for_user(user)
            return ResponseHandler.success(
                f"OTP verified successfully for {user.email}",
                {"access_token": tokens["access"]}
            )
        except Exception as exc:
            logger.exception("Token generation failed for user %s", user.user_id)
            return ResponseHandler.server_error("Internal server error")
        

class ResetPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Any) -> Any:
        new_password: str | None = request.data.get("new_password")
        confirm_password: str | None = request.data.get("confirm_password")

        if not new_password or not confirm_password:
            return ResponseHandler.bad_request("Both passwords are required")

        if new_password != confirm_password:
            return ResponseHandler.bad_request("Passwords do not match")

        user = request.user

        try:
            user.password = make_password(new_password)
            user.save(update_fields=["password"])

            UserAuth.objects.filter(user_id=user.user_id).update(
                otp=None,
                otp_expired_at=None
            )

            return ResponseHandler.success("Password reset successful")

        except Exception:
            logger.exception("Password reset failed for user %s", user.user_id)
            return ResponseHandler.server_error("Internal server error")
        
 
   
class SocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request: Any) -> Any:
        provider: str | None = request.data.get("provider")
        token: str | None = request.data.get("token")

        if not provider or not token:
            return ResponseHandler.bad_request("Provider and token are required")

        provider = provider.lower()
        if provider not in {"google", "apple"}:
            return ResponseHandler.bad_request("Unsupported provider")

        try:
            user_data: Optional[Dict[str, str]] = (
                decode_google_token(token) if provider == "google"
                else decode_apple_token(token)
            )

            if not user_data or not user_data.get("email"):
                return ResponseHandler.bad_request(f"Invalid {provider.capitalize()} token")

            email: str = user_data["email"]

            user, created = UserAuth.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": user_data.get("full_name", email.split("@")[0]),
                    "profile_pic_url": user_data.get("profile_pic_url"),
                    "is_verified": True,
                },
            )

            updated_fields = []
            if not created:
                if user.full_name != user_data.get("full_name", user.full_name):
                    user.full_name = user_data.get("full_name", user.full_name)
                    updated_fields.append("full_name")
                if user.profile_pic_url != user_data.get("profile_pic_url", user.profile_pic_url):
                    user.profile_pic_url = user_data.get("profile_pic_url", user.profile_pic_url)
                    updated_fields.append("profile_pic_url")
                if updated_fields:
                    user.save(update_fields=updated_fields)

            tokens = generate_tokens_for_user(user)

            serialized_user = UserSerializer(user, context={"request": request}).data

            message = (
                f"User created via {provider.capitalize()} login"
                if created else f"User logged in via {provider.capitalize()}"
            )

            return ResponseHandler.success(
                message,
                {"access_token": tokens["access"], "user": serialized_user}
            )

        except Exception as exc:
            logger.exception("Social login failed: %s", exc)
            return ResponseHandler.server_error("Internal server error")
        
        
class UserDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request: Any, user_id: int) -> Any:
        try:
            if not (request.user.is_superuser or request.user.user_id == user_id):
                return ResponseHandler.forbidden("You do not have permission to delete this user")

            try:
                user = UserAuth.objects.only("user_id", "email").get(user_id=user_id)
            except UserAuth.DoesNotExist:
                return ResponseHandler.not_found("User not found")

            user.delete()

            return ResponseHandler.deleted(f"User {user.email} deleted successfully")

        except Exception as exc:
            logger.exception("Failed to delete user %s", user_id)
            return ResponseHandler.server_error("Internal server error")
        
class GetUserInfoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response({
            'success': True,
            'message': 'User info retrieved successfully',
            'data': serializer.data
            }, status=status.HTTP_200_OK)