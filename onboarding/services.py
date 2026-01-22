from typing import List
from django.db import transaction
from .models import OnboardingStep, CoachingStyle

from typing import List
from django.db import transaction
from .models import OnboardingStep, CoachingStyle

class OnboardingService:
    @staticmethod
    @transaction.atomic
    def create_onboarding(user, coaching_style: CoachingStyle, focus: List[str]) -> OnboardingStep:
        if not coaching_style.is_active:
            raise ValueError("Coaching style does not exist")

        if hasattr(user, "onboarding"):
            raise ValueError("Onboarding already exists for this user")

        # Coaching style name will also auto-fill via model save
        onboarding = OnboardingStep.objects.create(
            user=user,
            coaching_style_id=coaching_style,
            focus=focus
        )
        return onboarding

    @staticmethod
    def get_onboarding(user) -> OnboardingStep:
        try:
            return user.onboarding
        except OnboardingStep.DoesNotExist:
            raise ValueError("Onboarding does not exist")
