from django.db.models.signals import post_save
from django.dispatch import receiver
from account.models import UserAuth
from .models import Notification

@receiver(post_save, sender=UserAuth)
def notify_user_creation(sender, instance: UserAuth, created:bool, **kwargs)-> None:
    if not created:
        return
    
    if created:
        Notification.objects.create(
            event = "User Created",
            title = "New User Registered",
            message = f"A new user with email {instance.email} has registered.",
            user_id = instance.user_id
        )
        
    