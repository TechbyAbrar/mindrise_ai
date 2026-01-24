from django.contrib import admin
from .models import CoachingStyle, OnboardingStep, TrackMood



@admin.register(CoachingStyle)
class CoachingStyleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "value", "is_active", "order", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "value")
    ordering = ("order",)
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("is_active", "order")



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



@admin.register(TrackMood)
class TrackMoodAdmin(admin.ModelAdmin):
    list_display = ("user", "mood_score", "mood_label", "mood_date")
    list_filter = ("mood_score", "mood_date")
    search_fields = ("user__username", "journal")
    ordering = ("-mood_date",)