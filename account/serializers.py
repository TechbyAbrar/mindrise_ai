from rest_framework import serializers
from .models import UserAuth
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
    profile_pic_url = serializers.SerializerMethodField(read_only=True)
    is_otp_valid = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserAuth
        fields = [
            "user_id",
            "email",
            "phone",
            "username",
            "full_name",
            "profile_pic",
            "profile_pic_url",
            "country",
            "bio",
            "is_verified",
            "is_active",
            "is_staff",
            "date_joined",
            "updated_at",
            "last_login",
            "otp", 
            "otp_expired_at", 
            "is_otp_valid",
        ]
        read_only_fields = [
            "user_id",
            "is_verified",
            "is_active",
            "is_staff",
            "date_joined",
            "updated_at",
            "last_login",
        ]

    def get_profile_pic_url(self, obj: UserAuth):
        if obj.profile_pic:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.profile_pic.url)
            return obj.profile_pic.url
        return None

    def get_is_otp_valid(self, obj: UserAuth):
        # returns True/False if OTP exists and is still valid
        if obj.otp and obj.otp_expired_at:
            return obj.otp_expired_at >= timezone.now()
        return False

    def validate_phone(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits.")
        return value

    def validate_otp(self, value):
        if value and len(value) != 6:
            raise serializers.ValidationError("OTP must be 6 digits.")
        return value
