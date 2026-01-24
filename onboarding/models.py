from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CoachingStyle(models.Model):
    value = models.CharField(max_length=20, unique=True, db_index=True)
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

    def save(self, *args, **kwargs):
        # Normalize value
        self.value = self.value.strip().lower()
        super().save(*args, **kwargs)


class OnboardingStep(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="onboarding",
        db_index=True
    )

    coaching_style_id = models.ForeignKey(
        CoachingStyle,
        on_delete=models.PROTECT,
        related_name="onboarding_steps"
    )
    
    coaching_style_value = models.CharField( 
        max_length=20,
        editable=False,
        blank=True,
        null=True,
        db_index=True,
        help_text="coaching style value snapshot at creation"
    )

    coaching_style_name = models.CharField(
        max_length=100,
        editable=False,
        blank=True,
        null=True,
        db_index=True,
        help_text="coaching style name snapshot at creation"
    )

    focus = models.JSONField(default=list, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        style_name = self.coaching_style_name or getattr(self.coaching_style_id, "name", "Unknown")
        return f"OnboardingStep(user={self.user_id}, style={style_name})"

    def save(self, *args, **kwargs):
        if self.coaching_style_id:
            self.coaching_style_value = self.coaching_style_id.value
            self.coaching_style_name = self.coaching_style_id.name
        super().save(*args, **kwargs)

    @property
    def coaching_style_info(self):
        return {
            "value": self.coaching_style_id.value if self.coaching_style_id else None,
            "name": self.coaching_style_name or (self.coaching_style_id.name if self.coaching_style_id else None)
        }

    @property
    def get_focus(self):
        return self.focus or []

class TrackMood(models.Model):
    MOOD_CHOICES = [
        (0, "Sad"),
        (1, "Unhappy"),
        (2, "Neutral"),
        (3, "Happy"),
        (4, "Very Happy"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="moods",
        db_index=True
    )

    mood_score = models.SmallIntegerField(
        choices=MOOD_CHOICES,
        db_index=True
    )

    feel = models.JSONField(
        default=list,
        blank=True,
        help_text="List of emotions or feelings associated with the mood"
    )

    journal = models.TextField(
        blank=True,
        help_text="Optional journal entry for the day"
    )

    mood_date = models.DateField(
        db_index=True,
        help_text="Date this mood represents (one entry per user per day)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

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
        verbose_name = "Mood Entry"
        verbose_name_plural = "Mood Entries"

    def __str__(self):
        return f"User:{self.user_id} | {self.mood_label} | {self.mood_date}"

    @property
    def mood_label(self) -> str:
        return dict(self.MOOD_CHOICES).get(self.mood_score, "Unknown")

    def add_feel(self, new_feel: str) -> None:
        if new_feel and new_feel not in self.feel:
            self.feel.append(new_feel)
            self.save(update_fields=["feel", "updated_at"])

    def remove_feel(self, remove_feel: str) -> None:
        if remove_feel in self.feel:
            self.feel.remove(remove_feel)
            self.save(update_fields=["feel", "updated_at"])


