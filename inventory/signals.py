from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Location

User = get_user_model()

@receiver(post_save, sender=User)
def create_default_location_for_new_user(sender, instance, created, **kwargs):
    """
    Create a default location for new users when they are created.
    """
    if created:
        # Create a default location for the new user
        default_location_name = f"{instance.username}'s Default Location"
        Location.objects.create(
            user=instance,
            name=default_location_name
        )
