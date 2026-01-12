from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import UserAuth


@admin.register(UserAuth)
class UserAuthAdmin(UserAdmin):
    model = UserAuth

    # Fields shown in user list
    list_display = (
        "user_id",
        "email",
        "full_name",
        "username",
        "phone",
        "is_active",
        "is_staff",
        "is_verified",
        "is_subscribed",
        "date_joined",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_verified",
        "date_joined",
    )

    search_fields = (
        "email",
        "full_name",
        "username",
        "phone",
    )

    ordering = ("-date_joined",)

    # Field layout in detail view
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {
            "fields": (
                "full_name",
                "username",
                "phone",
                "profile_pic",
                "country",
                "bio",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Status", {
            "fields": (
                "is_verified",
                "otp",
                "otp_expired_at",
            )
        }),
        ("Important Dates", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    # Fields used when creating a user via admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "full_name",
                "password1",
                "password2",
                "is_active",
                "is_staff",
            ),
        }),
    )

    readonly_fields = (
        "user_id",
        "date_joined",
        "last_login",
        "updated_at",
    )
