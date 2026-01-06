import random
import string
import secrets
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

import requests
import jwt
from PIL import Image
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import send_mail, BadHeaderError
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

try:
    import messagebird
except ImportError:
    messagebird = None

logger = logging.getLogger(__name__)

# ---------------------------
# OTP / Email Utilities
# ---------------------------
def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    return ''.join(secrets.choice("0123456789") for _ in range(length))


def get_otp_expiry(minutes: int = 30) -> timezone.datetime:
    """Return expiry timestamp for OTP."""
    return timezone.now() + timedelta(minutes=minutes)


def send_otp_email(recipient_email: str, otp: str) -> None:
    """Send an OTP to the user's email."""
    from_email = getattr(settings, "EMAIL_HOST_USER", None) or getattr(
        settings, "DEFAULT_FROM_EMAIL", None
    )
    if not from_email:
        raise ImproperlyConfigured(
            "Sender email not configured. Set EMAIL_HOST_USER or DEFAULT_FROM_EMAIL."
        )

    subject = "Verify Your Email"
    message = f"Your One-Time Password (OTP) is: {otp}"

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info("OTP email sent to %s", recipient_email)
    except BadHeaderError:
        logger.error("Invalid header found while sending OTP email to %s", recipient_email)
    except Exception as e:
        logger.exception("Error sending OTP email to %s: %s", recipient_email, e)


# ---------------------------
# SMS Utilities (MessageBird)
# ---------------------------
def send_otp_sms(phone: str, message: str) -> bool:
    """Send SMS using MessageBird API."""
    if not messagebird:
        logger.error("messagebird library not installed")
        return False
    try:
        client = messagebird.Client(settings.MESSAGEBIRD_API_KEY)
        response = client.message_create(
            originator=settings.DEFAULT_FROM_NUMBER,
            recipients=[phone],
            body=message
        )
        logger.info("MessageBird SMS sent to %s: %s", phone, response.id)
        return True
    except messagebird.client.ErrorException as e:
        logger.error("MessageBird API error: %s", e.errors)
        return False
    except Exception as e:
        logger.exception("Unexpected SMS send error for %s: %s", phone, e)
        return False


# ---------------------------
# Token Utilities
# ---------------------------
def generate_tokens_for_user(user) -> Dict[str, str]:
    """Generate JWT access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh)
    }


# ---------------------------
# Image Utilities
# ---------------------------
def validate_image(image) -> None:
    """Validate uploaded image size and format."""
    if image:
        max_size = 3 * 1024 * 1024  # 3MB
        allowed_formats = ["JPEG", "PNG", "GIF"]
        if image.size > max_size:
            raise ValidationError("Image file too large (max 3MB).")
        try:
            img = Image.open(image)
            img.verify()  # ensures image is not corrupted
            if img.format not in allowed_formats:
                raise ValidationError(
                    f"Unsupported image format: {img.format}. Allowed: {allowed_formats}"
                )
        except (OSError, ValueError) as e:
            raise ValidationError(f"Invalid image file: {e}")


# ---------------------------
# Username Utility
# ---------------------------
def generate_username(email: str) -> str:
    base = email.split("@")[0][:8]
    suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))
    return f"{base}{suffix}"


# ---------------------------
# Social Token Validators
# ---------------------------
def validate_facebook_token(access_token: str) -> Optional[Dict[str, Any]]:
    """Validate Facebook access token and return user info."""
    try:
        url = f"https://graph.facebook.com/me?fields=id,name,email&access_token={access_token}"
        response = requests.get(url, timeout=5)
        data = response.json()
        if "error" in data:
            logger.warning("Facebook token error: %s", data["error"])
            return None
        return data
    except Exception as e:
        logger.exception("Facebook token validation failed: %s", e)
        return None


def validate_google_token(id_token: str) -> Optional[Dict[str, Any]]:
    """Validate Google ID token and return minimal user info."""
    try:
        response = requests.get(
            f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token}", timeout=5
        )
        data = response.json()
        if "email" not in data:
            return None
        return {
            "email": data.get("email"),
            "full_name": data.get("name"),
            "profile_pic_url": data.get("picture")
        }
    except Exception as e:
        logger.exception("Google token validation failed: %s", e)
        return None


def validate_microsoft(access_token: str) -> Optional[Dict[str, Any]]:
    """Validate Microsoft access token and return minimal user info."""
    try:
        res = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        ).json()
        email = res.get("mail") or res.get("userPrincipalName")
        if not email:
            return None
        return {
            "email": email,
            "full_name": res.get("displayName"),
            "profile_pic_url": None
        }
    except Exception as e:
        logger.exception("Microsoft token validation failed: %s", e)
        return None


def validate_apple(identity_token: str) -> Optional[Dict[str, Any]]:
    """Decode Apple JWT identity token and return minimal user info.
    NOTE: For production, verify signature using Apple's public keys.
    """
    try:
        decoded = jwt.decode(identity_token, options={"verify_signature": False})
        email = decoded.get("email")
        if not email:
            return None
        return {
            "email": email,
            "full_name": decoded.get("name") or email.split("@")[0],
            "profile_pic_url": None
        }
    except Exception as e:
        logger.exception("Apple token validation failed: %s", e)
        return None
