from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    is_approved = models.BooleanField(default=False)  #  Must be approved by Admin
    
    def __str__(self):
        return f"{self.user.username} Profile"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


# Auto-create profile when a user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


# Auto-save profile when user is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Using hasattr to prevent errors if a user was created before this signal was set up
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)