from django.contrib import admin
from .models import CoachingStyle, OnboardingStep, TrackMood


# --------------------------------
# CoachingStyle Admin
# --------------------------------
@admin.register(CoachingStyle)
class CoachingStyleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "value", "is_active", "order", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "value")
    ordering = ("order",)
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("is_active", "order")


# --------------------------------
# OnboardingStep Admin
# --------------------------------
@admin.register(OnboardingStep)
class OnboardingStepAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "coaching_style_id",
        "coaching_style_name",
        "created_at",
    )
    list_filter = ("coaching_style_id",)
    search_fields = ("user__username", "coaching_style_name")
    readonly_fields = ("coaching_style_name", "created_at", "updated_at")
    ordering = ("-created_at",)


# --------------------------------
# TrackMood Admin
# --------------------------------
@admin.register(TrackMood)
class TrackMoodAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "mood_score",
        "mood_label",
        "mood_date",
        "created_at",
    )
    list_filter = ("mood_score", "mood_date")
    search_fields = ("user__username", "mood_label")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-mood_date",)

    # Optional: allow editing feel JSON inline safely
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("feel",)
        return self.readonly_fields
