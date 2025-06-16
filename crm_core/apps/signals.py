# apps/signals.py

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    जब भी कोई नया User बनता है, तो उसके लिए एक Profile बनाएं।
    """
    if created:
        # यह सुनिश्चित करें कि प्रोफाइल पहले से मौजूद नहीं है
        if not hasattr(instance, 'profile'):
            Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    जब भी User सेव होता है, तो उसका Profile भी सेव करें।
    """
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # अगर किसी वजह से प्रोफाइल नहीं बना था, तो अब बना दें
        Profile.objects.create(user=instance)