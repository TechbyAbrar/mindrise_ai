from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CoachingStyle(models.Model):
    value = models.CharField(max_length=20, unique=True,  db_index=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        db_table = 'coaching_styles'
        verbose_name = 'Coaching Style'
        verbose_name_plural = 'Coaching Styles'
    
    def __str__(self):
        return self.name
    
class OnboardingStep(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="onboarding",
        db_index=True
    )

    coaching_style = models.ForeignKey(
        CoachingStyle,
        on_delete=models.PROTECT,
        related_name="onboarding_steps"
    )

    focus = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OnboardingStep(user={self.user_id}, style={self.coaching_style.value})"


class TrackMood(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="moods", db_index=True)

    mood_score = models.SmallIntegerField(db_index=True)
    mood_label = models.CharField(max_length=155, blank=True)
    feel = models.JSONField(default=list, blank=True)
    journal = models.TextField(blank=True)

    mood_date = models.DateField(db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "mood_date"],
                name="unique_user_mood_per_day"
            )
        ]
        indexes = [
            models.Index(fields=["user", "mood_date"]),
            models.Index(fields=["user", "mood_score"]),
        ]
        ordering = ["-mood_date"]

    def __str__(self):
        return f"{self.user_id} | {self.mood_score}"

    def add_feel(self, new_feel):
        if new_feel not in self.feel:
            self.feel.append(new_feel)
            self.save(update_fields=["feel", "updated_at"])

    def remove_feel(self, remove_feel):
        if remove_feel in self.feel:
            self.feel.remove(remove_feel)
            self.save(update_fields=["feel", "updated_at"])
