from rest_framework import serializers
from .models import OnboardingStep, CoachingStyle

class OnboardingSerializer(serializers.ModelSerializer):
    # Input/output flat field
    coaching_style = serializers.SlugRelatedField(
        source='coaching_style_id',  # maps to actual FK
        slug_field='value',
        queryset=CoachingStyle.objects.filter(is_active=True)
    )

    coaching_style_name = serializers.CharField(read_only=True)

    class Meta:
        model = OnboardingStep
        fields = [
            "user_id",
            "coaching_style",
            "coaching_style_name",
            "focus",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user_id", "coaching_style_name", "created_at", "updated_at"]
