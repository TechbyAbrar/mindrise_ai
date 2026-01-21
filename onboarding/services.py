# services.py
from typing import List
from django.db import transaction
from .models import OnboardingStep, CoachingStyle

class OnboardingService:

    @staticmethod
    @transaction.atomic
    def create_onboarding(user_id: int, coaching_style: str, focus: List[str]) -> OnboardingStep:
        if not CoachingStyle.objects.filter(value=coaching_style, is_active=True).exists():
            raise ValueError("Coaching style does not exist")

        # Create onboarding; raise error if already exists
        onboarding, created = OnboardingStep.objects.get_or_create(
            user_id=user_id,
            coaching_style=coaching_style,
            defaults={"focus": focus}
        )

        if not created:
            raise ValueError("Onboarding already exists")

        return onboarding

    @staticmethod
    def get_onboarding(user_id: int, coaching_style: str) -> OnboardingStep:
        try:
            return OnboardingStep.objects.get(user_id=user_id, coaching_style=coaching_style)
        except OnboardingStep.DoesNotExist:
            raise ValueError("Onboarding does not exist")
