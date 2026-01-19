from django.contrib import admin
from .models import CoachingStyle, OnboardingStep, TrackMood


@admin.register(CoachingStyle)
class CoachingStyleAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "value")
    ordering = ("order",)
    list_editable = ("order", "is_active")


@admin.register(OnboardingStep)
class OnboardingStepAdmin(admin.ModelAdmin):
    list_display = ("user", "coaching_style", "created_at")
    list_filter = ("coaching_style",)
    search_fields = ("user__email", "user__username")
    autocomplete_fields = ("user",)
    date_hierarchy = "created_at"


@admin.register(TrackMood)
class TrackMoodAdmin(admin.ModelAdmin):
    list_display = ("user", "mood_score", "mood_label", "mood_date")
    list_filter = ("mood_score", "mood_date")
    search_fields = ("user__email", "user__username", "journal")
    autocomplete_fields = ("user",)
    date_hierarchy = "mood_date"
    ordering = ("-mood_date",)

    readonly_fields = ("created_at", "updated_at")
