"""
Authentication Models for Hotel Review Platform
Extends Django User model with hotel associations and role management
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with hotel association and role management"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Hotel Manager'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    hotel = models.ForeignKey(
        'reviews.Hotel', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Primary hotel association"
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='viewer',
        help_text="User role for permission management"
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Contact phone number"
    )
    department = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Department or position"
    )
    last_login_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="Last login IP address"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['hotel']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"
    
    def get_accessible_hotels(self):
        """Get hotels this user can access based on role"""
        if self.role == 'admin' or self.user.is_superuser:
            from apps.reviews.models import Hotel
            return Hotel.objects.all()
        elif self.hotel:
            return [self.hotel]
        else:
            return []
    
    def can_access_hotel(self, hotel):
        """Check if user can access specific hotel"""
        if self.role == 'admin' or self.user.is_superuser:
            return True
        return self.hotel == hotel
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role == 'admin' or self.user.is_superuser
    
    def can_upload_reviews(self):
        """Check if user can upload reviews"""
        return self.role in ['admin', 'manager'] or self.user.is_superuser
    
    def can_view_analytics(self):
        """Check if user can view analytics"""
        return True  # All authenticated users can view analytics
    
    @property
    def display_name(self):
        """Get display name for user"""
        return self.user.get_full_name() or self.user.username
    
    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin' or self.user.is_superuser

    @classmethod
    def ensure_profile_exists(cls, user):
        """Ensure a profile exists for the given user"""
        profile, created = cls.objects.get_or_create(user=user)
        return profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create user profile when user is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    try:
        if hasattr(instance, 'profile') and instance.profile:
            instance.profile.save()
        else:
            # Ensure profile exists
            UserProfile.objects.get_or_create(user=instance)
    except Exception:
        # If there's any issue with profile, create it
        UserProfile.objects.get_or_create(user=instance)