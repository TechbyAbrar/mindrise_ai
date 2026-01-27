from typing import List
from django.db import transaction
from .models import OnboardingStep, CoachingStyle, TrackMood
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

class OnboardingService:

    @staticmethod
    @transaction.atomic
    def create_onboarding(*, user, coaching_style: CoachingStyle, focus: list) -> OnboardingStep:
        if not coaching_style.is_active:
            raise ValueError("Selected coaching style is inactive")

        if OnboardingStep.objects.filter(user=user).exists():
            raise ValueError("Onboarding already exists for this user")

        return OnboardingStep.objects.create(
            user=user,
            coaching_style_id=coaching_style,
            focus=focus,
        )

    @staticmethod
    def get_onboarding(*, user) -> OnboardingStep:
        try:
            return OnboardingStep.objects.get(user=user)
        except OnboardingStep.DoesNotExist:
            raise ObjectDoesNotExist("Onboarding does not exist for this user")

    @staticmethod
    def onboarding_exists(*, user) -> bool:
        return OnboardingStep.objects.filter(user=user).exists()
    
    @staticmethod
    @transaction.atomic
    def upsert_onboarding(*, user, coaching_style, focus):
        onboarding, created = OnboardingStep.objects.update_or_create(
            user=user,
            defaults={
                "coaching_style_id": coaching_style,  # ✅ FIX
                "focus": focus,
            },
        )
        return onboarding, created


class TrackMoodService:

    @staticmethod
    def create(*, user, data):
        return TrackMood.objects.create(user=user, **data)

    @staticmethod
    def list(*, user):
        return TrackMood.objects.filter(user=user)

    @staticmethod
    def get(*, user, mood_id):
        return get_object_or_404(TrackMood, id=mood_id, user=user)

    @staticmethod
    def update(*, instance, data):
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    @staticmethod
    def delete(*, instance):
        instance.delete()