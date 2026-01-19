# serializers.py
from typing import List
from rest_framework import serializers

class OnboardingSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    coaching_style = serializers.CharField(max_length=20)
    focus = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )

    def validate_coaching_style(self, value: str) -> str:
        return value.strip().lower()
