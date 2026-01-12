from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .utils import  validate_image
from .services import generate_username
from .models import UserAuth
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuth
        fields = [
            "user_id",
            "email",
            "username",
            "full_name",
            "phone",
            "profile_pic",
            "profile_pic_url",
            "country",
            "bio",
            "is_verified",
            "is_active",
            "is_staff",
            "is_subscribed",
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "user_id",
            "is_verified",
            "is_active",
            "is_staff",
            "date_joined",
            "last_login",
        ]

    def validate_username(self, value: str) -> str:
        if value:
            qs = UserAuth.objects.filter(username__iexact=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("Username already in use.")
        return value

    def validate_profile_pic(self, value):
        if value:
            validate_image(value)
        return value


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, required=True)
    confirm_password = serializers.CharField(write_only=True, min_length=6, required=True)

    class Meta:
        model = UserAuth
        fields = [
            "email",
            "username",
            "full_name",
            "phone",
            "password",
            "confirm_password",
        ]

    def validate_email(self, value: str) -> str:
        qs = UserAuth.objects.filter(email__iexact=value)
        if qs.exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data: dict) -> UserAuth:
        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password")

        if not validated_data.get("username"):
            # Use utils to generate username
            username = generate_username(validated_data["email"])
            while UserAuth.objects.filter(username=username).exists():
                username = generate_username(validated_data["email"])
            validated_data["username"] = username

        user = UserAuth(**validated_data)
        user.set_password(password)
        user.save()
        return user


class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(otp=data["otp"], otp_expired_at__gte=timezone.now())
        except User.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid or expired OTP."})

        if user.is_verified:
            raise serializers.ValidationError({"otp": "User already verified."})

        data["user"] = user
        return data

    def save(self, **kwargs):
        user = self.validated_data["user"]
        from django.db import transaction
        with transaction.atomic():
            user.is_verified = True
            user.otp = None
            user.otp_expired = None
            user.save(update_fields=["is_verified", "otp", "otp_expired_at"])
        return user