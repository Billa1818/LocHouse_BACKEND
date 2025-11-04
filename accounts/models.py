# ============================================================================
# 1. APP: accounts
# ============================================================================

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    """Modèle utilisateur personnalisé"""
    USER_TYPE_CHOICES = (
        ('proprietaire', 'Propriétaire'),
        ('locataire', 'Locataire'),
        ('admin', 'Administrateur'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_name = models.CharField(max_length=200, blank=True, null=True)  # Ex: "Hôtel Dallas"
    is_identity_verified = models.BooleanField(default=False)
    identity_document = models.FileField(upload_to='identities/', blank=True, null=True)
    identity_verified_at = models.DateTimeField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.user_type})"


class OTPToken(models.Model):
    """Tokens OTP pour authentification email"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_tokens')
    token = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=(
        ('login', 'Connexion'),
        ('register', 'Inscription'),
    ))
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at


class UserSession(models.Model):
    """Gestion des sessions et appareils connectés"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    device_name = models.CharField(max_length=200)
    device_type = models.CharField(max_length=50)  # mobile, desktop, tablet
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    refresh_token = models.TextField(unique=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_activity']


