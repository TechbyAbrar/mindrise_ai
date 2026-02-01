# notifications/models.py
from django.db import models
from django.utils import timezone
from typing import Final

class Notification(models.Model):
    id = models.BigAutoField(primary_key=True)

    type: Final[str] = "USER_CREATED"
    event = models.CharField(max_length=50, db_index=True)

    title = models.CharField(max_length=255)
    message = models.TextField()

    user_id = models.BigIntegerField(null=True, blank=True, db_index=True)  # who triggered
    is_read = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return self.title
